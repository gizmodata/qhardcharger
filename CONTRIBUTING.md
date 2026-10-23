# Contributing to qhardcharger

Use Python 3.11 or later, QGIS 4 and imports from `qgis.PyQt` with fully scoped Qt 6 enums. Preserve the inherited GPL-2.0-or-later copyright notices.

```bash
python3.12 -m venv .venv
. .venv/bin/activate
pip install -r requirements/testing.txt flake8==7.4.1 bandit==1.9.4
python -m unittest discover -s tests/unit -v
python -m pytest tests/integration -v -m integration
flake8 qhardcharger
bandit -r qhardcharger --severity-level medium --exclude qhardcharger/embedded_external_libs
```

The integration fixture starts a local Hardcharger server with a temporary self-signed TLS certificate. In an environment with QGIS 4 and runtime dependencies, also run `python3 tests/qgis/verify_provider.py`; this exercises the actual provider and dialog, not QGIS stubs. The `qgis4` CI job uses the official QGIS checker container and runs the same test.

`python scripts/package_plugin.py` builds the slim `dist/qhardcharger.zip`, including the license and excluding native dependencies, caches and macOS resource forks. To build an offline Python 3.12 ZIP, install the pinned runtime dependencies into `qhardcharger/embedded_external_libs/`, then run `python scripts/package_plugin.py --offline <platform>`. Never commit native dependencies.

## Release

1. Update `qhardcharger/metadata.txt` version and changelog; keep `experimental=False` and the QGIS 4 version range.
2. Add the matching version section to `CHANGELOG.md`.
3. Push to main, then wait for every CI job to pass.
4. Tag `vX.Y.Z` matching metadata and push the tag. CI builds slim and platform-specific Python 3.12 offline ZIPs and creates the GitHub Release.
5. The publish job uploads the slim ZIP using the repository's `QGIS_PLUGIN_TOKEN` secret, scoped to the `qhardcharger` package. Create the empty package on plugins.qgis.org first. A successful API upload does not guarantee approval; inspect the plugin's review status.

No plugin token belongs in source, logs or release assets. A plugin repository failure leaves the independently installable GitHub Release available; retry only the failed publication job after fixing the problem.
