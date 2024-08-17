import asyncio
import logging
from datetime import datetime, timezone

from aiohttp import ClientSession

from sncf_max_tickets_checker.config import settings
from sncf_max_tickets_checker.email_sender import send_email_alert

# Configurer le logger
logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] in %(filename)s (line n°%(lineno)d) | %(asctime)s -> %(message)s')
logger = logging.getLogger(__name__)

# Collections MongoDB
alerts_collection = settings.mongo_db["alerts"]
sent_alerts_collection = settings.mongo_db["sent_alerts"]  # Collection pour les alertes envoyées avec UUID


class TicketFetcher:
    def __init__(self):
        self.base_url = settings.BASE_URL
        self.limit = -1
        self.order_by = 'date'
        self.timezone = 'Europe/Paris'
        self.lang = 'fr'

    async def fetch_tickets(self, where: str, session: ClientSession):
        """
        Fetch tickets from the API based on the provided query
        """
        tickets = []
        params = {
            'where': where,
            'limit': self.limit,
            'order_by': self.order_by,
            'timezone': self.timezone,
            'lang': self.lang
        }

        try:
            logger.info(f"Fetching tickets with params: {params}")
            async with session.get(self.base_url, params=params) as a_response:
                a_response.raise_for_status()
                json_response = await a_response.json()
                tickets.extend(json_response.get('results', []))

                # Pagination pour récupérer plus de tickets
                while len(tickets) > 0:
                    next_start_date = tickets[-1]['date']
                    params['where'] = f"{where} AND date > \"{next_start_date}\""
                    async with session.get(self.base_url, params=params) as b_response:
                        b_response.raise_for_status()
                        json_response = await b_response.json()

                        if len(json_response.get('results', [])) == 0:
                            break

                        tickets.extend(json_response.get('results', []))

                logger.info(f"Tickets fetched: {len(tickets)}")
                return tickets

        except Exception as e:
            logger.error(f"Error fetching tickets: {e}")
            return []

    def check_alerts(self, tickets):
        """
        Vérifie si les tickets récupérés correspondent aux alertes stockées dans MongoDB.
        Si une alerte correspond, vérifie si un email a déjà été envoyé pour ce ticket.
        Args:
            tickets (list): Liste des tickets récupérés.
        """
        for ticket in tickets:
            alerts = list(alerts_collection.find({
                "origine_iata": ticket['origine_iata'],
                "destination_iata": ticket['destination_iata'],
                "date": ticket['date']
            }))

            for alert in alerts:
                # Vérifier si la place est disponible pour "od_happy_card"
                if ticket["od_happy_card"] == "NON":
                    continue

                # Vérifier l'intervalle de temps si spécifié dans l'alerte
                if alert.get('heure_depart_debut') and alert.get('heure_depart_fin'):
                    heure_depart_ticket = datetime.strptime(ticket['heure_depart'], "%H:%M").time()
                    heure_depart_debut = datetime.strptime(alert['heure_depart_debut'], "%H:%M").time()
                    heure_depart_fin = datetime.strptime(alert['heure_depart_fin'], "%H:%M").time()

                    if not (heure_depart_debut <= heure_depart_ticket <= heure_depart_fin):
                        continue

                # Vérifier si un email a déjà été envoyé pour cette alerte en utilisant l'UUID
                if self.has_email_been_sent(alert['alert_id'], ticket):
                    logger.info(f"Email already sent for alert {alert['alert_id']} to {alert['email']}, skipping.")
                    continue

                # Si tout correspond et qu'aucun email n'a été envoyé, envoyer l'alerte par email
                send_email_alert(alert['email'], ticket)

                # Enregistrer que l'alerte a été envoyée pour ce ticket
                self.record_sent_alert(alert['alert_id'], ticket)

    def has_email_been_sent(self, alert_id: str, ticket: dict) -> bool:
        """
        Vérifie si un email a déjà été envoyé pour cette alerte (par UUID).
        Args:
            alert_id (str): L'UUID de l'alerte.
            ticket (dict): Informations sur le ticket.

        Returns:
            bool: True si l'email a déjà été envoyé, sinon False.
        """
        return sent_alerts_collection.find_one({
            "alert_id": alert_id,
            "train_no": ticket['train_no'],
            "date": ticket['date'],
            "heure_depart": ticket['heure_depart']
        }) is not None

    def record_sent_alert(self, alert_id: str, ticket: dict):
        """
        Enregistre qu'un email a été envoyé pour cette alerte (par UUID) afin d'éviter les doublons.
        Args:
            alert_id (str): L'UUID de l'alerte.
            ticket (dict): Informations sur le ticket.
        """
        sent_alerts_collection.insert_one({
            "alert_id": alert_id,
            "train_no": ticket['train_no'],
            "date": ticket['date'],
            "heure_depart": ticket['heure_depart'],
            "created_at": datetime.now(timezone.utc)
        })

    async def get_max_tickets(self, session: ClientSession):
        """
        Récupère les tickets et vérifie les alertes en boucle.
        """
        logger.info("Checking tickets for all alerts in MongoDB.")
        # Récupérer toutes les alertes de MongoDB
        alerts = list(alerts_collection.find())

        for alert in alerts:
            # Construire la requête pour chaque alerte
            where_clause = f"origine_iata=\"{alert['origine_iata']}\" AND destination_iata=\"{alert['destination_iata']}\""
            if alert.get('date'):
                where_clause += f" AND date>=\"{alert['date']}\" AND date<=\"{alert['date']}\""

            tickets = await self.fetch_tickets(where_clause, session)
            if tickets:
                self.check_alerts(tickets)


async def run_ticket_checker():
    """
    Exécute le ticket checker en boucle à intervalle régulier.
    """
    ticket_fetcher = TicketFetcher()

    # Créer une session HTTP réutilisable
    async with ClientSession() as session:
        while True:
            try:
                # Récupérer et vérifier les tickets pour chaque alerte
                await ticket_fetcher.get_max_tickets(session)
            except Exception as e:
                logger.error(f"Error during ticket checking: {e}")

            # Attendre 1 minute avant de vérifier à nouveau
            logger.info("Waiting for 1 minute before the next check...")
            await asyncio.sleep(60)  # 1 minutes


if __name__ == "__main__":
    # Démarrer la boucle d'événements asyncio
    try:
        logger.info("Starting the SNCF Max Tickets checker...")
        asyncio.run(run_ticket_checker())
    except KeyboardInterrupt:
        logger.info("Ticket checker stopped.")
