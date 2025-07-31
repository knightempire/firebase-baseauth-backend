import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=dotenv_path)


class Settings:
    CLOUDSQL_HOST = os.environ["CLOUDSQL_HOST"]
    CLOUDSQL_USER = os.environ["CLOUDSQL_USER"]
    CLOUDSQL_PASSWORD = os.environ["CLOUDSQL_PASSWORD"]
    CLOUDSQL_DB = os.environ["CLOUDSQL_DB"]
    ENV = os.environ["ENV"]
    JWT_SECRET = os.environ["JWT_SECRET"]
    JWT_ALGORITHM = os.environ["JWT_ALGORITHM"]
    ACCESS_TOKEN_EXPIRE_SECONDS = int(os.environ["ACCESS_TOKEN_EXPIRE_SECONDS"])
    REFRESH_TOKEN_EXPIRE_MINUTES = int(os.environ["REFRESH_TOKEN_EXPIRE_MINUTES"])
    FIREBASE_CREDS = {
        "type": os.environ["FIREBASE_TYPE"],
        "project_id": os.environ["FIREBASE_PROJECT_ID"],
        "private_key_id": os.environ["FIREBASE_PRIVATE_KEY_ID"],
        "private_key": os.environ["FIREBASE_PRIVATE_KEY"].replace('\\n', '\n'),
        "client_email": os.environ["FIREBASE_CLIENT_EMAIL"],
        "client_id": os.environ["FIREBASE_CLIENT_ID"],
        "auth_uri": os.environ["FIREBASE_AUTH_URI"],
        "token_uri": os.environ["FIREBASE_TOKEN_URI"],
        "auth_provider_x509_cert_url": os.environ["FIREBASE_AUTH_PROVIDER_X509_CERT_URL"],
        "client_x509_cert_url": os.environ["FIREBASE_CLIENT_X509_CERT_URL"],
        "universe_domain": os.environ["FIREBASE_UNIVERSE_DOMAIN"],
    }

settings = Settings()
