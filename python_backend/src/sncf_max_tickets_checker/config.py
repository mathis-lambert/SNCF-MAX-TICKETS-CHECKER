import logging
import os

from dotenv import load_dotenv
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] in %(filename)s (line n°%(lineno)d) | %(asctime)s -> %(message)s')
logger = logging.getLogger(__name__)

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()


class Settings:
    BASE_URL = os.getenv('MAX_TICKETS_BASE_URL')
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USER = os.getenv('SMTP_USER')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

    # Configuration MongoDB
    MONGO_HOST = os.getenv('MONGO_HOST')
    MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
    MONGO_USER = os.getenv('MONGO_USER')
    MONGO_PASSWORD = os.getenv('MONGO_PASSWORD')
    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME')

    def __init__(self):
        # Construction de l'URI avec nom d'utilisateur et mot de passe
        uri_with_auth = f"mongodb://{self.MONGO_USER}:{self.MONGO_PASSWORD}@{self.MONGO_HOST}:{self.MONGO_PORT}/{self.MONGO_DB_NAME}?authSource=admin"
        try:
            logger.info("Connexion à la base de données MongoDB avec les informations suivantes:")
            logger.info(f"URI: {uri_with_auth}")
            self.mongo_client = MongoClient(uri_with_auth)
            self.mongo_db = self.mongo_client[self.MONGO_DB_NAME]
            logger.info("Connexion à la base de données MongoDB établie.")
        except Exception as e:
            logger.error(f"Erreur lors de la connexion à la base de données MongoDB: {e}")
            exit(1)


# Créer une instance de Settings pour accéder aux configurations
settings = Settings()
