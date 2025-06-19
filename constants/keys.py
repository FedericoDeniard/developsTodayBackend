import os
from dotenv import load_dotenv

load_dotenv()

USER = os.getenv("DB_USER", "postgres")
PASSWORD = os.getenv("DB_PASSWORD", "federico")
HOST = os.getenv("DB_HOST", "localhost")
PORT = os.getenv("DB_PORT", "5432")
TARGET_DB = os.getenv("DB_NAME", "developsToday")

KEYS = {
    "USER": USER,
    "PASSWORD": PASSWORD,
    "HOST": HOST,
    "PORT": PORT,
    "TARGET_DB": TARGET_DB,
    "DATABASE_URL": f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{TARGET_DB}",
    "DEFAULT_DB_URL": f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/postgres"
}
