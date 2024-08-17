# Utiliser une image officielle de Python comme base
FROM python:3.9-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

COPY . .

# Installer les dépendances nécessaires
RUN pip install --no-cache-dir .

# Copier tout le code de l'application dans le répertoire de travail du conteneur

# Exposer le port 8000 pour accéder à l'application FastAPI
EXPOSE 9091

# Commande pour démarrer l'application FastAPI avec Uvicorn
CMD ["uvicorn", "sncf_max_tickets_checker.main:app", "--host", "0.0.0.0", "--port", "9091", "--reload"]
