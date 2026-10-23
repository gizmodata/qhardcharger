<p align="center">
  <a href="https://github.com/gizmodata/hardcharger">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/gizmodata/qhardcharger/main/docs/assets/hardcharger-banner-dark.png">
      <img src="https://raw.githubusercontent.com/gizmodata/qhardcharger/main/docs/assets/hardcharger-banner-light.png" alt="Hardcharger™" width="400">
    </picture>
  </a>
</p>

<p align="center">
  <a href="https://github.com/gizmodata/qhardcharger/actions/workflows/ci.yml"><img src="https://github.com/gizmodata/qhardcharger/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/gizmodata/qhardcharger/releases/latest/download/qhardcharger.zip"><img src="https://img.shields.io/github/v/release/gizmodata/qhardcharger?label=stable%20ZIP&amp;color=2563eb" alt="Download stable plugin ZIP"></a>
  <a href="https://plugins.qgis.org/plugins/qhardcharger/"><img src="https://img.shields.io/badge/QGIS-Plugin%20Repository-589632.svg?logo=qgis&amp;logoColor=white" alt="QGIS Plugin Repository"></a>
  <a href="https://qgis.org/download/"><img src="https://img.shields.io/badge/QGIS-4.2.3%2B-589632.svg?logo=qgis&amp;logoColor=white" alt="QGIS 4.2.3 or later"></a>
  <a href="https://github.com/gizmodata/qhardcharger#connect-and-add-a-layer"><img src="https://img.shields.io/badge/docs-Hardcharger-2563eb.svg" alt="Hardcharger QGIS guide"></a>
  <a href="https://github.com/gizmodata/hardcharger-adbc"><img src="https://img.shields.io/badge/ADBC-1.12-f15a24.svg" alt="ADBC 1.12"></a>
  <a href="https://github.com/gizmodata/warp-sql"><img src="https://img.shields.io/badge/protocol-Warp%20SQL-31a8db.svg" alt="Warp SQL protocol"></a>
  <img src="https://img.shields.io/badge/plugin-Python-3776AB.svg?logo=python&amp;logoColor=white" alt="Python plugin">
  <a href="https://github.com/gizmodata/hardcharger"><img src="https://img.shields.io/badge/server-Hardcharger-f15a24.svg" alt="Hardcharger"></a>
  <a href="https://github.com/gizmodata/qhardcharger/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-GPL%202.0%2B-brightgreen.svg" alt="GPL 2.0 or later license"></a>
  <a href="https://gizmodata.com"><img src="https://img.shields.io/badge/by-GizmoData%E2%84%A2-f15a24.svg" alt="GizmoData™"></a>
</p>

<h3 align="center">qhardcharger — visualize Hardcharger spatial data in QGIS 4.</h3>

---

Browse [Hardcharger](https://gizmodata.com/hardcharger) spatial tables and custom SQL directly in **QGIS 4.2.3 or later / Qt 6**. The read-only vector provider streams Arrow record batches through the native Hardcharger ADBC driver over **Warp SQL HTTP(S)**. Your data stays on the server.

Use the current stable QGIS 4.2.3 or later. The native Arrow C interface also works with QGIS’s already loaded Arrow libraries, including its reduced macOS PyArrow build, without importing the optional dataset module or replacing QGIS’s libraries.

Version 1.0.0 is a stable release (`experimental=False`). QGIS compatibility is declared as 4.2.3–4.99. This is a separate plugin from [qgizmosql](https://github.com/gizmodata/qgizmosql); it connects to Hardcharger, using its own provider key and settings.

## Install

1. Download [`qhardcharger.zip`](https://github.com/gizmodata/qhardcharger/releases/latest/download/qhardcharger.zip).
2. In QGIS 4, open **Plugins → Manage and Install Plugins → Install from ZIP**.
3. Select the ZIP and install. On activation, accept the dependency download into the plugin's own `embedded_external_libs/` folder.
4. Restart QGIS after upgrades, so Python reloads the native libraries and plugin code.

The slim ZIP uses the same package submitted to the [QGIS plugin repository](https://plugins.qgis.org/plugins/qhardcharger/). Availability in QGIS's searchable catalog depends on repository approval. No experimental-plugin setting is needed for this stable release.

**Offline installation:** releases also include Linux x86-64, macOS Apple silicon, and Windows x86-64 ZIPs with dependencies for **Python 3.12**. Match both your operating system and QGIS's Python version (shown under **Help → About**). Other Python versions should use the slim ZIP, which installs the correct wheels for the running interpreter. Runtime dependencies require Python 3.11 or later.

New installations pin NumPy 2.5.4 on Python 3.12+ (2.4.6 on Python 3.11), packaging 26.3, and: `adbc-driver-hardcharger==2.0.2`, `adbc-driver-manager==1.12.0`, `pyarrow==26.0.0`. QGIS may have already loaded its own compatible Arrow/NumPy versions; the provider uses their stable C interface rather than swapping native modules in a running application.

## Connect and add a layer

1. Open **Plugins → Hardcharger → Add Hardcharger layer**.
2. Enter the **Host** (a hostname, without a URI scheme) and **Port** (default `31337`). TLS/HTTPS is enabled by default. Turn it off only for a local development server without TLS.
3. For **Password** sign-in, select or create a **Basic authentication** configuration using the credentials selector. QGIS Auth Manager encrypts the password; projects store only the `authcfg` reference.
4. Alternatively, choose **OAuth / SSO (Enterprise Edition)** for browser sign-in to an appropriately configured server.
5. Click **Connect & list tables**, select a `catalog.schema.table`, and choose the actual **Geometry CRS** of your data.
6. Click **Add Layer**. Use **Custom SQL** to load a SELECT query instead of a table.

The provider discovers DuckDB spatial `GEOMETRY` columns (including typed geometry columns). Set the CRS to match the source coordinates; assigning a CRS does not transform the data. Numeric single-column primary keys are used as feature IDs; other layers receive generated IDs. Subset SQL, simple expressions, bounding boxes, feature IDs and attribute selections are handled by the provider.

For local self-signed certificates, **Skip TLS cert verification** is available. Leave it disabled for production.

## Try a local server

Install the server and client in a separate Python environment:

```bash
pip install 'hardcharger[adbc]==2.0.1'
```

Run this script and leave it running while connecting from QGIS. Install and load the spatial extension as an administrator before using spatial functions.

```python
import hardcharger

with hardcharger.Server(username="hardcharger", password="local-example-only") as server:
    with server.connect() as conn, conn.cursor() as cur:
        cur.execute("INSTALL spatial")
        cur.execute("LOAD spatial")
        cur.execute("CREATE TABLE cities (id BIGINT PRIMARY KEY, name VARCHAR, geom GEOMETRY)")
        cur.execute("INSERT INTO cities VALUES "
                    "(1, 'Charlotte', ST_Point(-80.8431, 35.2271)), "
                    "(2, 'London', ST_Point(-0.1276, 51.5074))")
    print(f"QGIS host: {server.host}, port: {server.port}; disable TLS for this local server")
    input("Press Enter when finished... ")
```

Add the `cities` table with **EPSG:4326**.

## PyQGIS scripting

After activating the plugin, run in QGIS's Python console:

```python
from qgis.core import QgsProject, QgsProviderRegistry, QgsVectorLayer

metadata = QgsProviderRegistry.instance().providerMetadata("hardcharger")
uri = metadata.encodeUri({
    "host": "db.example.com",
    "port": "31337",
    "authcfg": "abc1234",  # your QGIS Basic authentication config ID
    "schema": "main",
    "table": "cities",
    "epsg": "4326",
})
layer = QgsVectorLayer(uri, "Cities", "hardcharger")
if not layer.isValid():
    raise RuntimeError("Check the Hardcharger entry in QGIS Log Messages")
QgsProject.instance().addMapLayer(layer)
```

Layer URIs use `hardcharger://host:port?use_tls=1&authcfg=...&schema=main&table=cities&epsg=4326`. They also accept `tls=false` for compatibility with driver URIs. Catalog defaults to `current_database()`; pass `catalog` to address another attached catalog. Table, schema and catalog names currently accept ASCII SQL identifiers (`[A-Za-z_][A-Za-z0-9_]*`); use custom SQL with quoted identifiers for other names. For custom SQL, replace `table`/`schema` with `sql: "SELECT id, name, geom FROM main.cities WHERE id > 0"`.

## Troubleshooting

- **Missing dependencies:** accept the first-run download, or install an offline ZIP matching your platform and Python version. Restart QGIS after reinstalling.
- **Connection refused:** check the server address, port and whether TLS is enabled on both ends.
- **No geometry:** the source query must return a native `GEOMETRY` column. Convert WKB with `ST_GeomFromWKB` in custom SQL if necessary.
- **Invalid layer or query:** check **View → Panels → Log Messages → Hardcharger**. Ensure your user can read the selected table.
- **Saved project on another computer:** create the matching QGIS Auth Manager configuration there before opening the layer.

## Development and release

See [CONTRIBUTING.md](CONTRIBUTING.md) for tests, packaging and publication. CI runs unit and live-server tests across Python 3.11–3.15, Qt 6 migration checks, and real QGIS 4 provider tests. OAuth requires an identity provider and is not part of the automated sign-in tests.

## Credits and license

Derived from **[qgizmosql](https://github.com/gizmodata/qgizmosql)** by GizmoData and **[QDuckDB](https://gitlab.com/Oslandia/qgis/qduckdb)** by Oslandia, originally funded by IFREMER. Original authors and copyright notices are preserved. **GPL-2.0-or-later**; see [LICENSE](LICENSE). The Hardcharger ADBC driver and Apache Arrow dependencies have their own licenses.

[Issues](https://github.com/gizmodata/qhardcharger/issues) · [GizmoData](https://gizmodata.com) · [Hardcharger documentation](https://docs.hardcharger.gizmodata.com)
