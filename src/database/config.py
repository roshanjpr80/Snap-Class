import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def get_supabase_client() -> Client:
    """
    Returns a cached Supabase client.

    Cached with @st.cache_resource so a new client (and new network
    connection) isn't created on every single Streamlit rerun — this is
    the officially recommended pattern for stateful resources like DB
    clients in a Streamlit app.
    """
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_SECRET_KEY"]
    except KeyError as exc:
        st.error(
            "Missing Supabase configuration. Make sure SUPABASE_URL and "
            "SUPABASE_SECRET_KEY are set in .streamlit/secrets.toml "
            "(locally) or in your deployment's Secrets settings."
        )
        raise RuntimeError(f"Missing required Streamlit secret: {exc}") from exc

    return create_client(url, key)


# Import `supabase` from this module wherever you need DB access, e.g.:
#   from src.db.client import supabase
#   supabase.table("students").select("*").execute()
supabase: Client = get_supabase_client()