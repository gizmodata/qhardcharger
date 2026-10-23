"""Small ADBC/Arrow client using the standard Arrow C Data Interface.

QGIS macOS bundles PyArrow without the dataset extension. ADBC's DB-API wrapper
imports that optional extension even for simple SQL, so use the native ADBC
handles directly. No dataset, pandas or NumPy APIs are needed by this provider.
"""

from __future__ import annotations

import weakref

import adbc_driver_manager as adbc
from adbc_driver_hardcharger import DatabaseOptions
from adbc_driver_hardcharger._driver import _driver_path
import pyarrow as pa


class Connection:
    def __init__(self, database, connection):
        self._database = database
        self._connection = connection
        self._cursors = weakref.WeakSet()

    def cursor(self):
        if self._connection is None:
            raise RuntimeError("Connection is closed")
        cursor = Cursor(self)
        self._cursors.add(cursor)
        return cursor

    def close(self):
        for cursor in list(self._cursors):
            cursor.close()
        if self._connection is not None:
            self._connection.close()
            self._connection = None
        if self._database is not None:
            self._database.close()
            self._database = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class Cursor:
    def __init__(self, connection):
        self._connection = connection
        self._statement = None
        self._reader = None
        self._rows = iter(())
        self.description = None

    def execute(self, operation, parameters=None):
        self.close()
        self._statement = adbc.AdbcStatement(self._connection._connection)
        try:
            self._statement.set_sql_query(operation)
            if parameters is not None:
                batch = pa.record_batch(
                    [pa.array([value]) for value in parameters],
                    names=[str(i) for i in range(len(parameters))],
                )
                schema, array = batch.__arrow_c_array__()
                self._statement.bind(array, schema)
            stream, _ = self._statement.execute_query()
            self._reader = pa.RecordBatchReader._import_from_c(stream.address)
            self.description = [
                (field.name, field.type, None, None, None, None, field.nullable)
                for field in self._reader.schema
            ]
        except BaseException:
            self.close()
            raise
        return self

    def fetchone(self):
        if self._reader is None:
            return None
        while True:
            row = next(self._rows, None)
            if row is not None:
                return row
            try:
                batch = self._reader.read_next_batch()
            except StopIteration:
                return None
            self._rows = iter(zip(*(column.to_pylist() for column in batch.columns)))

    def fetchall(self):
        rows = []
        while True:
            row = self.fetchone()
            if row is None:
                return rows
            rows.append(row)

    def fetch_record_batch(self):
        return self._reader

    def fetch_arrow_table(self):
        return self._reader.read_all()

    def close(self):
        if self._reader is not None:
            self._reader.close()
            self._reader = None
        if self._statement is not None:
            self._statement.close()
            self._statement = None
        self._rows = iter(())

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        self.close()


def connect(uri, username=None, password=None, auth_type="password", tls_skip_verify=False):
    options = {"uri": uri}
    if username is not None:
        options["username"] = username
    if password is not None:
        options["password"] = password
    if auth_type != "password":
        options[DatabaseOptions.AUTH_TYPE.value] = auth_type
    if tls_skip_verify:
        options[DatabaseOptions.TLS_SKIP_VERIFY.value] = "true"
    database = adbc.AdbcDatabase(driver=_driver_path(), **options)
    try:
        connection = adbc.AdbcConnection(database)
    except BaseException:
        database.close()
        raise
    return Connection(database, connection)
