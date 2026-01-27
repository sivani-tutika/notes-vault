import os

# JWT / auth settings
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-to-a-random-secret-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24))  # 1 day

# Streamlit settings (defaults)
STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", 8501))
