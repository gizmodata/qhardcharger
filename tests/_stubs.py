"""Install minimal stubs for the ``qgis.*`` and ``adbc_driver_*`` symbols
the wrapper touches at import time, so tests can run on a host without
QGIS / ADBC installed (CI lint job, basic dev box, etc.).

Both unit and integration tests call ``install()`` before importing
``qhardcharger.provider.hardcharger_wrapper``. Integration tests then *replace*
the stubbed ``adbc_driver_hardcharger`` with the real package on sys.path,
because they need to actually open a Warp SQL connection.
"""

from __future__ import annotations

import os
import sys
import types

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _ensure_repo_on_sys_path() -> None:
    if REPO_ROOT not in sys.path:
        sys.path.insert(0, REPO_ROOT)


def install() -> None:
    """Idempotent: install qgis + ADBC stubs if not already present."""
    _ensure_repo_on_sys_path()

    if "qgis.core" not in sys.modules:
        qgis = types.ModuleType("qgis")
        qgis_core = types.ModuleType("qgis.core")

        class _MessageLevel:
            NoLevel = 0
            Info = 1
            Warning = 2
            Critical = 3
            Success = 4

        class _Qgis:
            MessageLevel = _MessageLevel

        class _QgsApplication:
            @staticmethod
            def authManager():
                return None

        class _QgsAuthMethodConfig:
            def __init__(self):
                self._cfg = {}

            def config(self, key):
                return self._cfg.get(key)

        qgis_core.Qgis = _Qgis
        qgis_core.QgsApplication = _QgsApplication
        qgis_core.QgsAuthMethodConfig = _QgsAuthMethodConfig
        sys.modules.setdefault("qgis", qgis)
        sys.modules["qgis.core"] = qgis_core

    if "qhardcharger.toolbelt.log_handler" not in sys.modules:
        log_handler_mod = types.ModuleType("qhardcharger.toolbelt.log_handler")

        class _PlgLogger:
            @staticmethod
            def log(**kwargs):
                pass

        log_handler_mod.PlgLogger = _PlgLogger
        sys.modules["qhardcharger.toolbelt.log_handler"] = log_handler_mod

    if "pyarrow" not in sys.modules:
        try:
            import pyarrow
        except ImportError:
            arrow = types.ModuleType("pyarrow")
            arrow.__path__ = []
            sys.modules["pyarrow"] = arrow
            sys.modules["pyarrow.dataset"] = types.ModuleType("pyarrow.dataset")

    # adbc_driver_hardcharger may or may not be on sys.path. Stub only when
    # the real one is absent so integration tests pick up the real driver.
    if "adbc_driver_hardcharger" not in sys.modules:
        try:
            import adbc_driver_hardcharger  # noqa: F401
        except ImportError:
            adbc_pkg = types.ModuleType("adbc_driver_hardcharger")
            adbc_dbapi = types.ModuleType("adbc_driver_hardcharger.dbapi")
            adbc_dbapi.connect = lambda *a, **kw: None
            adbc_pkg.dbapi = adbc_dbapi

            class _DatabaseOptions:
                class WITH_MAX_MSG_SIZE:
                    value = "adbc.flight.sql.client_option.with_max_msg_size"

            adbc_pkg.DatabaseOptions = _DatabaseOptions
            sys.modules["adbc_driver_hardcharger"] = adbc_pkg
            sys.modules["adbc_driver_hardcharger.dbapi"] = adbc_dbapi
