import streamlit as st
import requests

# Safely read API_BASE from Streamlit secrets if present, otherwise fall back to localhost
API_BASE = "http://localhost:8000"
used_default_api_base = True
try:
    # st.secrets may raise StreamlitSecretNotFoundError if no secrets file exists
    secrets = st.secrets
    try:
        API_BASE = secrets.get("API_BASE", API_BASE)
        used_default_api_base = (API_BASE == "http://localhost:8000")
    except Exception:
        # If secrets behaves unexpectedly, keep default
        used_default_api_base = True
except Exception:
    # If st.secrets is not available for any reason, use default
    API_BASE = "http://localhost:8000"
    used_default_api_base = True

st.title("Notes Vault")

# Display currently used API base for debugging / visibility
st.sidebar.markdown("**API base**")
st.sidebar.write(API_BASE)
if used_default_api_base:
    st.sidebar.warning("Using the default API_BASE (http://localhost:8000).\nCreate a `.streamlit/secrets.toml` with API_BASE if your API is running elsewhere.")

# Helper: truncate password to 72 UTF-8 bytes (bcrypt limit)
BCRYPT_MAX_BYTES = 72

def _truncate_password(password: str) -> (str, bool):
    """Return (safe_password, was_truncated) where safe_password's UTF-8 encoding is <=72 bytes.

    If truncation occurred, the trailing partial character is dropped.
    """
    if password is None:
        return "", False
    if not isinstance(password, str):
        password = str(password)
    b = password.encode("utf-8")
    if len(b) <= BCRYPT_MAX_BYTES:
        return password, False
    truncated = b[:BCRYPT_MAX_BYTES]
    safe = truncated.decode("utf-8", errors="ignore")
    return safe, True

if "token" not in st.session_state:
    st.session_state.token = None

# Helper functions for API calls
def api_request(method, path, json=None, data=None):
    headers = {}
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    url = f"{API_BASE}{path}"
    try:
        resp = requests.request(method, url, headers=headers, json=json, data=data, timeout=10)
    except Exception as e:
        st.error(f"Request to {url} failed: {e}")
        return None
    return resp

def api_post(path, json=None, data=None):
    return api_request('POST', path, json=json, data=data)

def api_get(path):
    return api_request('GET', path)

# Authentication UI
st.sidebar.header("Auth")
mode = st.sidebar.selectbox("Mode", ["Login", "Signup"])
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

# Show truncation warning if needed
if password:
    _, was_truncated = _truncate_password(password)
    if was_truncated:
        st.sidebar.warning("Password is longer than 72 UTF-8 bytes and will be truncated before sending to the server.")

if mode == "Signup":
    if st.sidebar.button("Create account"):
        safe_pw, _ = _truncate_password(password)
        payload = {"username": username, "password": safe_pw}
        resp = api_post("/users/", json=payload)
        if resp is not None and resp.status_code == 200:
            st.sidebar.success("Account created. You can now log in.")
        else:
            msg = resp.text if resp is not None else "no response"
            st.sidebar.error(f"Signup failed: {msg}")
else:
    if st.sidebar.button("Log in"):
        # OAuth2 password flow expects form data. Truncate password similarly to how backend will hash it.
        safe_pw, _ = _truncate_password(password)
        resp = requests.post(f"{API_BASE}/users/token", data={"username": username, "password": safe_pw})
        if resp is not None and resp.status_code == 200:
            data = resp.json()
            st.session_state.token = data.get("access_token")
            st.sidebar.success("Logged in")
        else:
            msg = resp.text if resp is not None else "no response"
            st.sidebar.error(f"Login failed: {msg}")

# Notes UI: fetch and show all notes for the current user with CRUD actions

def fetch_notes():
    resp = api_get("/notes/")
    if resp is None:
        return []
    if resp.status_code == 200:
        try:
            return resp.json()
        except Exception:
            return []
    else:
        st.error(f"Failed to fetch notes: {resp.text}")
        return []


def delete_note(note_id: int):
    resp = api_request('DELETE', f"/notes/{note_id}")
    if resp is not None and resp.status_code == 200:
        st.success("Note deleted")
        return True
    else:
        st.error(f"Failed to delete note: {resp.text if resp is not None else 'no response'}")
        return False


def update_note(note_id: int, title: str, content: str):
    payload = {"title": title, "content": content}
    resp = api_request('PUT', f"/notes/{note_id}", json=payload)
    if resp is not None and resp.status_code == 200:
        st.success("Note updated")
        return True
    else:
        st.error(f"Failed to update note: {resp.text if resp is not None else 'no response'}")
        return False


def create_note_ui(title: str, content: str):
    payload = {"title": title, "content": content}
    resp = api_post("/notes/", json=payload)
    if resp is not None and resp.status_code == 200:
        st.success("Note created")
        return True
    else:
        st.error(f"Failed to create note: {resp.text if resp is not None else 'no response'}")
        return False


# Main area
if st.session_state.token:
    st.header("Your notes")

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Refresh"):
            # no-op; streamlit will re-run and re-fetch notes
            pass
    with col2:
        st.write("You are logged in. Use the form below to create a new note.")

    # Create note form
    with st.form(key="create_note_form"):
        new_title = st.text_input("Title", key="new_title")
        new_content = st.text_area("Content", key="new_content")
        if st.form_submit_button("Create note"):
            if create_note_ui(new_title, new_content):
                st.experimental_rerun()

    notes = fetch_notes()
    if not notes:
        st.info("No notes found. Create one using the form above.")
    else:
        for note in notes:
            note_id = note.get("id")
            title = note.get("title")
            content = note.get("content")
            created = note.get("created_at")

            with st.expander(f"{title} (id: {note_id})"):
                st.write(content)
                st.write(f"Created: {created}")

                # Edit fields
                edit_title = st.text_input("Edit title", value=title, key=f"title_{note_id}")
                edit_content = st.text_area("Edit content", value=content or "", key=f"content_{note_id}")
                edit_col1, edit_col2 = st.columns([1, 1])
                with edit_col1:
                    if st.button("Save", key=f"save_{note_id}"):
                        if update_note(note_id, edit_title, edit_content):
                            st.experimental_rerun()
                with edit_col2:
                    if st.button("Delete", key=f"delete_{note_id}"):
                        if delete_note(note_id):
                            st.experimental_rerun()

else:
    st.info("Please log in or sign up from the sidebar to manage notes.")

# End of file
