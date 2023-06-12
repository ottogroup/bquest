import google.auth as google_auth
from google.auth.exceptions import DefaultCredentialsError

try:
    _, GOOGLE_PROJECT_ID = google_auth.default()
except DefaultCredentialsError:
    GOOGLE_PROJECT_ID = None
