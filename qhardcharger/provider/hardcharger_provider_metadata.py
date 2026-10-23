"""QGIS provider metadata for the qhardcharger plugin.

The URI shape is owned by :mod:`qhardcharger.provider.hardcharger_wrapper` — see
``HardchargerTools.parse_uri`` / ``HardchargerTools.build_uri``. We delegate here so
there is a single source of truth for URI encoding/decoding.
"""

from typing import Dict
from urllib.parse import parse_qsl, urlencode, urlparse

from qgis.core import Qgis, QgsDataProvider, QgsProviderMetadata, QgsReadWriteContext

from qhardcharger.provider.hardcharger_provider import HardchargerProvider


class HardchargerProviderMetadata(QgsProviderMetadata):
    def __init__(self):
        super().__init__(
            HardchargerProvider.providerKey(),
            HardchargerProvider.description(),
        )

    def createProvider(self, uri, options, flags=QgsDataProvider.ReadFlags()):
        return HardchargerProvider(uri, options, flags)

    def supportedLayerTypes(self):
        return [Qgis.LayerType.Vector]

    def decodeUri(self, uri: str) -> Dict[str, str]:
        """Break the qhardcharger URI into a dict of string components."""
        parsed = urlparse(uri)
        result: Dict[str, str] = dict(parse_qsl(parsed.query, keep_blank_values=True))
        if parsed.hostname:
            result["host"] = parsed.hostname
        if parsed.port:
            result["port"] = str(parsed.port)
        return result

    def encodeUri(self, parts: Dict[str, str]) -> str:
        """Reassemble a qhardcharger URI from a component dict.

        Required keys: ``host``. Optional: ``port`` (default 31337),
        ``use_tls``, ``tls_skip_verify``, ``auth_type``, ``authcfg``,
        ``username``, ``password``, ``catalog``, ``schema``, ``table``,
        ``sql``, ``epsg``. ``catalog`` defaults to the connection's
        ``current_database()`` when omitted.
        """
        host = parts.get("host")
        if not host:
            raise ValueError("encodeUri: missing required 'host' part")
        port = parts.get("port", "31337")

        query = {k: v for k, v in parts.items() if k not in ("host", "port") and v}
        if query.get("authcfg"):
            query.pop("username", None)
            query.pop("password", None)
        authority = f"[{host}]" if ":" in host else host
        return f"hardcharger://{authority}:{port}?{urlencode(query)}"

    def absoluteToRelativeUri(self, uri: str, context: QgsReadWriteContext) -> str:
        """No-op — qhardcharger URIs are remote (no filesystem path to rewrite)."""
        return uri

    def relativeToAbsoluteUri(self, uri: str, context: QgsReadWriteContext) -> str:
        return uri
