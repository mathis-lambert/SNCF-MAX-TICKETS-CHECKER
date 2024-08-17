import uuid
from typing import List

from aiohttp import ClientSession
from fastapi import APIRouter, BackgroundTasks, HTTPException
from bson import ObjectId

import logging

from sncf_max_tickets_checker.models import Alert, Client
from sncf_max_tickets_checker.ticket_fetcher import TicketFetcher
from sncf_max_tickets_checker.config import settings  # Import MongoDB settings

logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] in %(filename)s (line n°%(lineno)d) | %(asctime)s -> %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter()

# Collection MongoDB pour les clients
clients_collection = settings.mongo_db["clients"]
alerts_collection = settings.mongo_db["alerts"]

@router.get("/alerts/", response_model=List[Alert])
async def get_alerts(email: str):
    """
    Récupère la liste des alertes pour un utilisateur donné.

    Args:
        email (str): Adresse email de l'utilisateur.

    Returns:
        List[Alert]: Liste des alertes définies par l'utilisateur.
    """
    client = clients_collection.find_one({"email": email})

    if client:
        # Récupérer les alertes liées à cet email
        alerts = list(alerts_collection.find({"email": email}))
        if alerts:
            for alert in alerts:
                alert["_id"] = str(alert["_id"])  # Convertir ObjectId en chaîne de caractères
            return alerts
    raise HTTPException(status_code=404, detail="Aucune alerte trouvée pour cet utilisateur.")


@router.delete("/alerts/")
async def delete_alert(email: str, alert_id: str):
    """
    Supprime une alerte définie par l'utilisateur.

    Args:
        email (str): Adresse email de l'utilisateur.
        alert_id (str): Id de l'alerte à supprimer.

    Returns:
        dict: Message confirmant la suppression ou indiquant que l'alerte n'a pas été trouvée.
    """
    alert = alerts_collection.find_one({"_id": ObjectId(alert_id), "email": email})

    if alert:
        result = alerts_collection.delete_one({"_id": ObjectId(alert_id)})
        if result.deleted_count > 0:
            return {"message": "Alerte supprimée avec succès."}
        else:
            raise HTTPException(status_code=404, detail="Échec de la suppression.")
    else:
        raise HTTPException(status_code=404, detail="Alerte non trouvée.")


@router.post("/start-checking/")
async def start_checking(alert: Alert):
    """
    Crée une nouvelle alerte et démarre la vérification des tickets en tâche de fond.
    """
    client = clients_collection.find_one({"email": alert.email})

    if not client:
        # Si le client n'existe pas, créer un nouveau client
        client_id = str(uuid.uuid4())
        new_client = Client(email=alert.email, client_id=client_id, alerts=[alert])
        clients_collection.insert_one(new_client.dict())
    else:
        # Si le client existe, ajouter l'alerte
        client_id = client["client_id"]
        clients_collection.update_one(
            {"email": alert.email},
            {"$push": {"alerts": alert.dict()}}
        )

    # Insérer l'alerte dans la collection MongoDB
    alert_id = alerts_collection.insert_one(alert.dict()).inserted_id

    return {"message": f"Checking started, alert_id: {str(alert_id)}"}

