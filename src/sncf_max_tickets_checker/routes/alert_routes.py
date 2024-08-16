from aiohttp import ClientSession
from fastapi import APIRouter, BackgroundTasks

from sncf_max_tickets_checker.models import Alert, Client
from sncf_max_tickets_checker.ticket_fetcher import TicketFetcher
import uuid

router = APIRouter()

clients = {}


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
