import uuid
from typing import List

from aiohttp import ClientSession
from fastapi import APIRouter, BackgroundTasks, HTTPException

from sncf_max_tickets_checker.models import Alert, Client
from sncf_max_tickets_checker.ticket_fetcher import TicketFetcher

router = APIRouter()

clients = {}


@router.get("/alerts/", response_model=List[Alert])
async def get_alerts(email: str):
    """
    Récupère la liste des alertes pour un utilisateur donné.

    Args:
        email (str): Adresse email de l'utilisateur.

    Returns:
        List[Alert]: Liste des alertes définies par l'utilisateur.
    """
    for client in clients.values():
        if client.email == email:
            return client.alerts

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
    for client in clients.values():
        if client.email == email:
            user_alerts = client.alerts
            alert_to_delete = None

            # Rechercher l'alerte à supprimer
            for alert in user_alerts:
                if alert.alert_id == alert_id:
                    alert_to_delete = alert
                    break

            if alert_to_delete:
                user_alerts.remove(alert_to_delete)
                return {"message": "Alerte supprimée avec succès."}

            return {"message": "Alerte non trouvée."}

    return {"message": "Aucune alerte trouvée pour cet utilisateur."}


@router.post("/start-checking/")
async def start_checking(alert: Alert, background_tasks: BackgroundTasks):
    if alert.email not in clients:
        client_id = str(uuid.uuid4())
        clients[client_id] = Client(email=alert.email, client_id=client_id, alerts=[alert])
    else:
        client_id = [client_id for client_id, client in clients.items() if client.email == alert.email][0]
        clients[client_id].alerts.append(alert)

    ticket_fetcher = TicketFetcher()
    ticket_fetcher.set_params(alert.origine_iata, alert.destination_iata)

    # Initialiser ClientSession dans un contexte asynchrone
    async def fetch_tickets_task():
        async with ClientSession() as session:
            await ticket_fetcher.get_max_tickets(session,
                                                 f"origine_iata=\"{alert.origine_iata}\" AND destination_iata=\"{alert.destination_iata}\"",
                                                 clients)

    # Ajouter la tâche asynchrone de vérification des tickets
    background_tasks.add_task(fetch_tickets_task)

    return {"message": f"Checking started, alert_id: {alert.alert_id}"}
