import logging
from datetime import datetime

from aiohttp import ClientSession

from sncf_max_tickets_checker.config import settings
from sncf_max_tickets_checker.email_sender import send_email_alert

logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] in %(filename)s (line n°%(lineno)d) | %(asctime)s -> %(message)s')
logger = logging.getLogger(__name__)


class TicketFetcher:
    def __init__(self):
        self.base_url = settings.BASE_URL
        self.fetched_tickets_cache = []
        self.available_tickets = []
        self.origine_iata = None
        self.destination_iata = None
        self.limit = -1
        self.order_by = 'date'
        self.timezone = 'Europe/Paris'
        self.lang = 'fr'

    def set_params(self, origine_iata: str, destination_iata: str, limit: int = -1, order_by: str = 'date',
                   timezone: str = 'Europe/Paris', lang: str = 'fr'):
        self.origine_iata = origine_iata
        self.destination_iata = destination_iata
        self.limit = limit
        self.order_by = order_by
        self.timezone = timezone
        self.lang = lang

    async def fetch_tickets(self, where: str, session: ClientSession):
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
            logger.info(f"Fetching tickets from: {self.base_url}")
            logger.info(f"Fetching tickets with client session: {session}")
            async with session.get(self.base_url, params=params) as response:
                response.raise_for_status()
                json_response = await response.json()
                for ticket in json_response.get('results', []):
                    tickets.append(ticket)

                while True:
                    next_start_date = tickets[-1]['date']
                    params['where'] = f"{where} AND date > \"{next_start_date}\""
                    async with session.get(self.base_url, params=params) as response:
                        response.raise_for_status()
                        json_response = await response.json()

                        if len(json_response.get('results', [])) == 0:
                            break

                        for ticket in json_response.get('results', []):
                            tickets.append(ticket)

                logger.info(f"Tickets fetched: {len(tickets)}")
                return tickets

        except Exception as e:
            # logger.error(f"Error fetching tickets: {e}")
            raise ValueError(e)
            return None

    def check_alerts(self, tickets, clients):
        """
        Vérifie si les tickets récupérés correspondent aux alertes définies.

        Args:
            tickets (list): Liste des tickets récupérés.
            clients (dict): Dictionnaire des clients avec leurs alertes.
        """
        for ticket in tickets:
            for client in clients.values():
                for alert in client.alerts:
                    # Vérifier l'origine, la destination et la date
                    if ticket["od_happy_card"] == "NON":
                        continue

                    if (ticket['origine_iata'] == alert.origine_iata and
                            ticket['destination_iata'] == alert.destination_iata and
                            ticket['date'] == alert.date):

                        # Vérifier l'intervalle de temps si spécifié
                        if alert.heure_depart_debut and alert.heure_depart_fin:
                            heure_depart_ticket = datetime.strptime(ticket['heure_depart'], "%H:%M").time()
                            heure_depart_debut = datetime.strptime(alert.heure_depart_debut, "%H:%M").time()
                            heure_depart_fin = datetime.strptime(alert.heure_depart_fin, "%H:%M").time()

                            # Si l'heure de départ ne correspond pas à l'intervalle, passer à l'alerte suivante
                            if not (heure_depart_debut <= heure_depart_ticket <= heure_depart_fin):
                                continue

                        send_email_alert(alert.email, ticket)

    async def get_max_tickets(self, session: ClientSession, where: str, clients):
        tickets = await self.fetch_tickets(where, session)
        if tickets:
            self.check_alerts(tickets, clients)
