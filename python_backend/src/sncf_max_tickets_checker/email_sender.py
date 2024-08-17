import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sncf_max_tickets_checker.config import settings

logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] in %(filename)s (line n°%(lineno)d) | %(asctime)s -> %(message)s')
logger = logging.getLogger(__name__)


def send_email_alert(to_email: str, ticket: dict):
    """
    Envoie un email d'alerte à un client via le serveur SMTP.

    Args:
        to_email (str): Adresse email du destinataire.
        subject (str): Sujet de l'email.
        body (str): Corps de l'email.
    """

    subject = f"Place MAX pour le train n°{ticket['train_no']} de {ticket['origine']} à {ticket['destination']} le {ticket['date']} à {ticket['heure_depart']}"

    # Corps de l'email au format HTML
    body = f"""
      <html>
      <body>
          <h1>Nouvelle place MAX pour un train SNCF</h1>
          <p>Voici les détails du train :</p>
          <ul>
              <li><strong>Origine :</strong> {ticket['origine']} ({ticket['origine_iata']})</li>
              <li><strong>Destination :</strong> {ticket['destination']} ({ticket['destination_iata']})</li>
              <li><strong>Numéro du train :</strong> {ticket['train_no']}</li>
              <li><strong>Heure de départ :</strong> {ticket['heure_depart']}</li>
              <li><strong>Heure d'arrivée :</strong> {ticket['heure_arrivee']}</li>
              <li><strong>Date :</strong> {ticket['date']}</li>
          </ul>
          <p>Réservez dès maintenant votre billet en cliquant sur le lien suivant :</p>
          <a href="https://www.sncf-connect.com/app/redirect?redirection_type=TRIP_IMPORT" target="_blank">
              Réservez sur SNCF Connect
          </a>
          <br><br>
          <p>Si vous n'avez pas encore l'application SNCF Connect, vous pouvez la télécharger ici :</p>
          <ul>
              <li><a href="https://apps.apple.com/fr/app/sncf-connect-trains-trajets/id343889987?ppid=3cf9afb7-bb5d-4dfd-babf-3f577c46076f" target="_blank">Télécharger sur l'App Store</a></li>
              <li><a href="https://play.google.com/store/apps/details?id=com.vsct.vsc.mobile.horaireetresa.android" target="_blank">Télécharger sur Google Play</a></li>
          </ul>
          <p>Merci d'utiliser mon service d'alerte.</p>
          <p>À bientôt !</p>
          <br>
          <pre>Ceci est un email automatique, merci de ne pas y répondre.</pre>
          <br>
            <hr>
            <p>Vous recevez cet email car vous avez souscrit à une alerte SNCF.</p>
            <p>Vous pouvez vous désinscrire à tout moment en supprimant votre alerte sur le site.</p>
            <hr>
            <p>© {datetime.now().year} Mathis LAMBERT. Tous droits réservés.</p>
            <p>Adresse de contact : contact.mathislambert@gmail.com</p>
      </body>
      </html>
      """

    try:
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        # html
        msg.attach(MIMEText(body, 'html'))

        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_USER, to_email, msg.as_string())

        logger.info(f"Email alert sent to {to_email}.")
    except Exception as e:
        logger.error(f"Failed to send email alert: {e}")
