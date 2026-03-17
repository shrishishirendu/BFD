"""
Microsoft Graph delegated authentication service using MSAL.
Handles OAuth 2.0 authorization code flow for Streamlit.
"""

import streamlit as st
import msal
import requests
from config import (
    AZURE_TENANT_ID,
    AZURE_CLIENT_ID,
    AZURE_CLIENT_SECRET,
    AZURE_AUTHORITY,
    AZURE_REDIRECT_URI,
    GRAPH_SCOPES,
    GRAPH_ME_URL,
)


def _build_msal_app(cache=None) -> msal.ConfidentialClientApplication:
    """Create an MSAL ConfidentialClientApplication instance."""
    return msal.ConfidentialClientApplication(
        client_id=AZURE_CLIENT_ID,
        client_credential=AZURE_CLIENT_SECRET,
        authority=AZURE_AUTHORITY,
        token_cache=cache,
    )


def _get_token_cache() -> msal.SerializableTokenCache:
    """Retrieve or create a token cache stored in session state."""
    if "token_cache" not in st.session_state:
        st.session_state["token_cache"] = msal.SerializableTokenCache()
    return st.session_state["token_cache"]


def get_auth_url() -> str:
    """Generate the Microsoft login URL for the authorization code flow."""
    app = _build_msal_app()
    return app.get_authorization_request_url(
        scopes=GRAPH_SCOPES,
        redirect_uri=AZURE_REDIRECT_URI,
    )


def acquire_token_by_code(auth_code: str) -> dict:
    """
    Exchange an authorization code for an access token.
    Returns the MSAL token response dict.
    """
    cache = _get_token_cache()
    app = _build_msal_app(cache=cache)
    result = app.acquire_token_by_authorization_code(
        code=auth_code,
        scopes=GRAPH_SCOPES,
        redirect_uri=AZURE_REDIRECT_URI,
    )
    if "access_token" in result:
        st.session_state["access_token"] = result["access_token"]
        st.session_state["authenticated"] = True
    return result


def get_access_token_silent() -> str | None:
    """
    Try to get a cached access token silently.
    Returns the token string or None.
    """
    cache = _get_token_cache()
    app = _build_msal_app(cache=cache)
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(GRAPH_SCOPES, account=accounts[0])
        if result and "access_token" in result:
            st.session_state["access_token"] = result["access_token"]
            st.session_state["authenticated"] = True
            return result["access_token"]
    return st.session_state.get("access_token")


def get_current_user(access_token: str) -> dict:
    """Fetch the signed-in user's profile from Microsoft Graph."""
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(GRAPH_ME_URL, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


def is_authenticated() -> bool:
    """Check whether the session has a valid access token."""
    return bool(st.session_state.get("authenticated", False))


def sign_out():
    """Clear authentication state from the session."""
    for key in ["access_token", "authenticated", "token_cache", "user_info"]:
        st.session_state.pop(key, None)


def is_configured() -> bool:
    """Check whether Azure credentials are configured."""
    return bool(AZURE_TENANT_ID and AZURE_CLIENT_ID and AZURE_CLIENT_SECRET)
