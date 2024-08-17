import os

from dotenv import load_dotenv

load_dotenv()


# Charger les variables d'environnement depuis le fichier .env
class Settings:
    BASE_URL = os.getenv('MAX_TICKETS_BASE_URL')
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USER = os.getenv('SMTP_USER')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')


settings = Settings()
