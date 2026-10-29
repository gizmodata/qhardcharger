# qhardcharger

Stable Hardcharger vector provider for QGIS 4 / Qt 6, derived from qgizmosql and Oslandia QDuckDB. GPL-2.0-or-later.

- Package/repository: `qhardcharger`; display name: `Hardcharger`; provider: `hardcharger`.
- Chargewire HTTP(S) via `adbc-driver-hardcharger`; never send Flight SQL options or gRPC URIs.
- Runtime pins live only in `qhardcharger/requirements.txt`; other requirements include that file.
- Credentials go through QGIS Auth Manager. When `authcfg` is supplied, never serialize raw credentials or fall back to unrelated credentials.
- QGIS 4 only: `qgisMinimumVersion=4.2.3`, `qgisMaximumVersion=4.99`, `experimental=False`.
- Qt imports: `qgis.PyQt`; QAction is in QtGui. Use fully scoped enums and QMetaType field types.
- Read CONTRIBUTING.md for verification and release. Actual QGIS integration tests are in `tests/qgis/verify_provider.py`.
- Keep metadata version and both changelogs current. CI requires the release tag to match metadata.
- Platform offline ZIPs target Python 3.12 explicitly. The slim ZIP downloads the wheels matching the running interpreter.

The macOS QGIS 4.2.3 build preloads NumPy 2.5.2 and reduced PyArrow 25.0.1 without dataset support. Use `provider/adbc_client.py` (ADBC C handles + Arrow C Data Interface), not the DB-API wrapper which unconditionally imports dataset. Never unload/replace already imported Arrow/NumPy modules. Fresh environments use the latest stable pins in requirements.txt.
