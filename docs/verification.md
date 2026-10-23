# qhardcharger 1.0.0 verification

Verified on 2026-10-23 against the released Hardcharger 2.0.0 server (Python launcher 2.0.1) and Hardcharger ADBC 2.0.2.

- QGIS 4.2.3 / Qt 6 on macOS Apple silicon: 12 real provider tests pass, including tables, custom SQL, spatial filtering, reprojection, attribute selection, null dates, 64-bit IDs, iterator rewind, empty/invalid sources, non-numeric/composite keys, encrypted Basic authentication and project serialization.
- The actual first-run installer downloads the pinned runtime dependencies with QGIS's Python. Dependency probing, `classFactory(iface)`, `initGui()` and `unload()` pass in an isolated QGIS profile.
- The official QGIS checker container runs Qt 6 migration checks and the same live provider tests in CI on Linux. CI also runs unit tests and TLS-backed live server tests across Python 3.11–3.15, plus lint/security checks.
- Offline artifacts are built for Linux x86-64, macOS arm64 and Windows x86-64, explicitly for Python 3.12. This is packaging coverage; native QGIS GUI execution was verified on macOS and Linux, not Windows.
- Browser OAuth/SSO is wired through the native driver's authentication option. An external identity provider is required; it is not covered by these sign-in tests.

New runtime installations pin ADBC Driver Manager 1.12.0, PyArrow 26.0.0, NumPy 2.5.4 (2.4.6 on Python 3.11), and packaging 26.3. The macOS QGIS build preloads NumPy 2.5.2 and reduced PyArrow 25.0.1 without the dataset module. The provider uses native ADBC handles and the stable Arrow C Data Interface with those loaded libraries; it never unloads or replaces native modules in the running QGIS process.

The minimum supported QGIS version is 4.2.3; the plugin's version range is 4.2.3–4.99. Installation from a GitHub ZIP is independent of QGIS repository review. Check the release workflow and the repository's plugin status before describing a store version as approved.
