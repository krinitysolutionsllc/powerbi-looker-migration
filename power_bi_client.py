"""Power BI REST helpers: PowerBIAppClient (app + secret) or PowerBIUserClient (browser sign-in)."""

from pathlib import Path
from typing import Any, Self

import httpx
import msal

PBI_SCOPE = "https://analysis.windows.net/powerbi/api/.default"
PBI_BASE = "https://api.powerbi.com/v1.0/myorg"


class _PowerBIHttpBase:
    """Shared httpx wiring and call(); subclasses implement _access_token()."""

    def __init__(self) -> None:
        self._http = httpx.Client(timeout=60.0)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _access_token(self) -> str:
        raise NotImplementedError

    def call(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        """Call the Power BI REST API with an access token from MSAL. Resolves a relative url under https://api.powerbi.com/v1.0/myorg, merges the bearer token into headers, and sends the request via httpx.

        Args:
            method: HTTP method to use (e.g. get, post, put, patch, delete). Case-insensitive.
            url: Full https URL to any Power BI endpoint, or a path segment only (e.g. groups, groups/{workspace_id}/reports). If not absolute, it is appended after .../v1.0/myorg/.
            **kwargs: Optional arguments passed through to httpx (e.g. params, json, content, headers, timeout). Extra headers are merged with the token header; Authorization is always set from MSAL.

        Returns:
            httpx Response for the HTTP call (check status or call raise_for_status() on it).
        """
        token = self._access_token()
        extra = kwargs.pop("headers", None) or {}
        headers = {**extra, "Authorization": f"Bearer {token}"}
        full_url = url if url.startswith("http") else f"{PBI_BASE}/{url.lstrip('/')}"
        return self._http.request(method.upper(), full_url, headers=headers, **kwargs)


class PowerBIAppClient(_PowerBIHttpBase):
    """Call the Power BI REST API using client credentials in Microsoft Entra (application id, tenant id, and client secret from your app registration). MSAL obtains access tokens; call() issues authenticated HTTP requests through httpx.

    Context manager: use a with-statement (with PowerBIAppClient(...) as pbi) so the httpx client is closed when the block ends and connections are released. Leaving the block runs the same cleanup as close(). If you construct the client without with, call close() yourself when finished.

    Typical usage is with PowerBIAppClient(app_id, tenant_id, secret) as pbi, then pbi.call("get", "groups") and handle the returned response.

    Args:
        app_id: Application (client) ID of the Entra app registration.
        tenant_id: Directory (tenant) ID for login.microsoftonline.com.
        client_secret: Client secret value for the confidential client (not the secret id).
    """

    def __init__(self, app_id: str, tenant_id: str, client_secret: str) -> None:
        super().__init__()
        self._app = msal.ConfidentialClientApplication(
            app_id,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
            client_credential=client_secret,
        )

    def _access_token(self) -> str:
        result = self._app.acquire_token_for_client(scopes=[PBI_SCOPE])
        if "access_token" not in result:
            msg = result.get("error_description") or result.get("error") or str(result)
            raise RuntimeError(msg)
        return result["access_token"]


class PowerBIUserClient(_PowerBIHttpBase):
    """Sign in with your personal Microsoft work/school account via the system browser (delegated token). Use this for My workspace and other user-scoped APIs.

    In Entra, register a Mobile and desktop redirect URI (e.g. http://localhost) for this app, enable delegated Power BI API permissions, and grant admin consent if required.

    The first run opens a browser; later runs reuse token_cache_file until refresh is needed.

    Args:
        app_id: Application (client) ID of the Entra app registration.
        tenant_id: Directory (tenant) ID.
        token_cache_file: Path to persist the MSAL token cache, or None to keep tokens in memory only.
    """

    def __init__(
        self,
        app_id: str,
        tenant_id: str,
        *,
        token_cache_file: str | None = ".msal_token_cache.json",
    ) -> None:
        super().__init__()
        self._cache_path = token_cache_file
        self._cache = msal.SerializableTokenCache()
        if self._cache_path:
            path = Path(self._cache_path)
            if path.is_file():
                self._cache.deserialize(path.read_text(encoding="utf-8"))
        self._app = msal.PublicClientApplication(
            app_id,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
            token_cache=self._cache,
        )

    def _persist_cache(self) -> None:
        if self._cache_path and self._cache.has_state:
            Path(self._cache_path).write_text(self._cache.serialize(), encoding="utf-8")

    def _access_token(self) -> str:
        result = None
        accounts = self._app.get_accounts()
        if accounts:
            result = self._app.acquire_token_silent([PBI_SCOPE], account=accounts[0])
        if not result:
            result = self._app.acquire_token_interactive(scopes=[PBI_SCOPE])
        self._persist_cache()
        if "access_token" not in result:
            msg = result.get("error_description") or result.get("error") or str(result)
            raise RuntimeError(msg)
        return result["access_token"]
