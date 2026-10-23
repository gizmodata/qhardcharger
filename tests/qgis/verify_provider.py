"""Real QGIS 4 integration tests. Run in a QGIS Python environment, without stubs."""

import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# Every credential created here belongs to a disposable test profile.
AUTH_DIR = tempfile.TemporaryDirectory(prefix="qhardcharger-auth-")
os.environ.setdefault("QGIS_AUTH_DB_DIR_PATH", AUTH_DIR.name)

import pyarrow
import hardcharger
from qgis.core import (
    Qgis, QgsApplication, QgsAuthMethodConfig, QgsFeature, QgsFeatureRequest,
    QgsProject, QgsProviderRegistry, QgsRectangle, QgsVectorLayer,
)
from qgis.PyQt.QtCore import QMetaType

APP = QgsApplication.instance()
if APP is None:
    APP = QgsApplication([], False)
    APP.initQgis()

from qhardcharger.gui.dlg_add_hardcharger_layer import LoadHardchargerLayerDialog
from qhardcharger.provider.hardcharger_provider_metadata import HardchargerProviderMetadata
from qhardcharger.provider.hardcharger_wrapper import HardchargerConnConfig, HardchargerTools
from qhardcharger.provider.adbc_client import connect


class TestQgis4Provider(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if Qgis.QGIS_VERSION_INT < 40000:
            raise RuntimeError("These tests require QGIS 4")
        registry = QgsProviderRegistry.instance()
        cls.metadata = HardchargerProviderMetadata()
        if registry.providerMetadata("hardcharger") is None:
            if not registry.registerProvider(cls.metadata):
                raise RuntimeError("Unable to register Hardcharger provider")
        cls.server = hardcharger.Server()
        cls.server.start()
        cls.config = HardchargerConnConfig(
            host=cls.server.host, port=cls.server.port, use_tls=False,
            username=cls.server.username, password=cls.server.password,
        )
        with connect(uri=cls.server.uri, username=cls.server.username,
                     password=cls.server.password) as conn, conn.cursor() as cur:
            cur.execute("INSTALL spatial")
            cur.execute("LOAD spatial")
            cur.execute("CREATE TABLE cities (name VARCHAR, id BIGINT PRIMARY KEY, "
                        "geom GEOMETRY, visited DATE)")
            cur.execute("INSERT INTO cities VALUES "
                        "('Charlotte',1099511627777,ST_Point(-80.8431,35.2271),DATE '2026-10-23'),"
                        "('London',1099511627778,ST_Point(-0.1276,51.5074),NULL),"
                        "('Tokyo',1099511627779,ST_Point(139.6917,35.6895),DATE '2026-10-22')")
            cur.execute("CREATE TABLE empty_cities AS SELECT * FROM cities WHERE false")
            cur.execute("CREATE TABLE labels AS SELECT name, id FROM cities")
            cur.execute("CREATE TABLE string_keys (name VARCHAR PRIMARY KEY, geom GEOMETRY)")
            cur.execute("INSERT INTO string_keys VALUES ('one',ST_Point(1,2))")
            cur.execute("CREATE TABLE composite_keys (a INTEGER,b INTEGER,geom GEOMETRY,"
                        "PRIMARY KEY (a,b))")
            cur.execute("INSERT INTO composite_keys VALUES (10,20,ST_Point(1,2))")
        print(f"Testing QGIS {Qgis.QGIS_VERSION}", flush=True)
        cls.layers = []

    @classmethod
    def tearDownClass(cls):
        QgsProject.instance().removeAllMapLayers()
        for layer in cls.layers:
            layer.dataProvider().disconnect_database()
        cls.layers.clear()
        cls.server.stop()

    def layer(self, table="cities", sql=None, config=None):
        uri = HardchargerTools.build_uri(
            config or self.config, table=None if sql else table,
            schema=None if sql else "main", sql=sql, epsg="4326",
        )
        layer = QgsVectorLayer(uri, "Test", "hardcharger")
        self.assertTrue(layer.isValid(), layer.error().message())
        self.layers.append(layer)
        return layer

    def test_spatial_table_and_bigint_primary_key(self):
        layer = self.layer()
        self.assertEqual(layer.featureCount(), 3)
        self.assertEqual(layer.fields().names(), ["name", "id", "visited"])
        self.assertEqual(layer.fields()[1].type(), QMetaType.Type.LongLong)
        features = list(layer.getFeatures())
        self.assertEqual([f.id() for f in features], [1099511627777,1099511627778,1099511627779])
        self.assertEqual(features[0]["name"], "Charlotte")
        self.assertAlmostEqual(features[0].geometry().asPoint().x(), -80.8431)
        self.assertEqual(features[0]["visited"].year(), 2026)
        self.assertTrue(layer.crs().isGeographic())
        self.assertAlmostEqual(layer.extent().xMaximum(),139.6917)

    def test_custom_sql(self):
        layer = self.layer(sql="SELECT id,name,geom FROM cities WHERE name != 'Tokyo';")
        self.assertEqual(layer.featureCount(),2)
        self.assertEqual({f["name"] for f in layer.getFeatures()},{"Charlotte","London"})
        self.assertEqual(layer.fields().names(),["id","name"])

    def test_invalid_sources_are_rejected(self):
        for options in ({"table": "missing_table"}, {"sql": "SELECT missing FROM cities"}):
            with self.subTest(options=options):
                uri = HardchargerTools.build_uri(self.config, schema="main", **options)
                layer = QgsVectorLayer(uri, "Invalid", "hardcharger")
                self.assertFalse(layer.isValid())

    def test_empty_layer_extent(self):
        layer = self.layer(table="empty_cities")
        self.assertEqual(layer.featureCount(),0)
        self.assertTrue(layer.extent().isNull())
        self.assertEqual(list(layer.getFeatures()),[])

    def test_attribute_only_table(self):
        layer = self.layer(table="labels")
        features = list(layer.getFeatures())
        self.assertEqual(len(features),3)
        self.assertFalse(features[0].hasGeometry())
        self.assertEqual(features[0]["name"],"Charlotte")

    def test_subset_sql_and_attribute_selection(self):
        layer = self.layer()
        self.assertTrue(layer.setSubsetString('"name" = \'London\''))
        self.assertEqual(layer.featureCount(),1)
        request = QgsFeatureRequest().setSubsetOfAttributes([1])
        features = list(layer.getFeatures(request))
        self.assertEqual([f["id"] for f in features],[1099511627778])
        self.assertTrue(layer.setSubsetString(""))
        self.assertEqual(layer.featureCount(),3)

    def test_feature_id_and_no_geometry(self):
        layer = self.layer()
        request = QgsFeatureRequest().setFilterFid(1099511627778)
        request.setSubsetOfAttributes([0])
        request.setFlags(request.flags() | QgsFeatureRequest.Flag.NoGeometry)
        features = list(layer.getFeatures(request))
        self.assertEqual(len(features),1)
        self.assertEqual(features[0]["name"],"London")
        self.assertFalse(features[0].hasGeometry())

    def test_bbox_and_expression(self):
        layer = self.layer()
        request = QgsFeatureRequest().setFilterRect(QgsRectangle(-1,50,1,53))
        self.assertEqual([f["name"] for f in layer.getFeatures(request)],["London"])
        request = QgsFeatureRequest().setFilterExpression('"name" = \'Tokyo\'')
        self.assertEqual([f["name"] for f in layer.getFeatures(request)],["Tokyo"])

    def test_iterator_rewind(self):
        layer = self.layer()
        iterator = layer.getFeatures()
        first = QgsFeature()
        self.assertTrue(iterator.nextFeature(first))
        self.assertTrue(iterator.rewind())
        again = QgsFeature()
        self.assertTrue(iterator.nextFeature(again))
        self.assertEqual(first.id(),again.id())
        iterator.close()

    def test_non_numeric_and_composite_keys(self):
        for table in ("string_keys","composite_keys"):
            with self.subTest(table=table):
                features = list(self.layer(table=table).getFeatures())
                self.assertEqual(len(features),1)
                self.assertIsInstance(features[0].id(),int)

    def test_auth_manager_dialog_and_project(self):
        manager = QgsApplication.authManager()
        manager.setPasswordHelperEnabled(False)
        self.assertTrue(manager.setMasterPassword("qhardcharger-test-only",True))
        cfg = QgsAuthMethodConfig()
        cfg.setName("qhardcharger integration test")
        cfg.setMethod("Basic")
        cfg.setConfig("username",self.server.username)
        cfg.setConfig("password",self.server.password)
        ok,cfg = manager.storeAuthenticationConfig(cfg)
        self.assertTrue(ok)
        config = HardchargerConnConfig(host=self.server.host,port=self.server.port,
                                       use_tls=False,authcfg=cfg.id())
        layer = self.layer(config=config)
        self.assertEqual(layer.featureCount(),3)
        metadata = QgsProviderRegistry.instance().providerMetadata("hardcharger")
        uri = metadata.encodeUri({"host":self.server.host,"authcfg":cfg.id(),
                                  "username":"unsafe-user","password":"unsafe-password"})
        self.assertNotIn("password=",uri)
        self.assertNotIn("username=",uri)
        project = QgsProject.instance()
        project.addMapLayer(layer)
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"test.qgs"
            self.assertTrue(project.write(str(path)))
            xml=path.read_text()
            self.assertNotIn(self.server.password,xml)
            self.assertIn("authcfg",xml)
        project.removeMapLayer(layer.id())
        self.layers.remove(layer)
        dialog=LoadHardchargerLayerDialog()
        dialog._host_edit.setText(self.server.host)
        dialog._port_spin.setValue(self.server.port)
        dialog._use_tls_cb.setChecked(False)
        dialog._authcfg_select.setConfigId(cfg.id())
        dialog._on_connect_clicked()
        self.assertIn("Connected",dialog._status_label.text())
        self.assertTrue(dialog._add_layer_btn.isEnabled())
        dialog._wrapper.close()
        dialog.close()
        manager.removeAuthenticationConfig(cfg.id())


if __name__ == "__main__":
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(TestQgis4Provider)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
