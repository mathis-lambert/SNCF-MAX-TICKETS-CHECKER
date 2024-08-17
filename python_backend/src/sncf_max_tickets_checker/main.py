import asyncio

import uvicorn
from fastapi import FastAPI

from sncf_max_tickets_checker.routes import alert_routes
from sncf_max_tickets_checker.ticket_fetcher import run_ticket_checker  # Importer la fonction qui vérifie les tickets

app = FastAPI()

# Enregistrement des routes
app.include_router(alert_routes.router)


# Démarrage de la vérification en continu lors de l'événement de démarrage de FastAPI
@app.on_event("startup")
async def start_ticket_checker():
    # Lancer le checker de tickets en arrière-plan
    _ = asyncio.create_task(run_ticket_checker())


# Ajout d'un événement pour fermer proprement la session HTTP à l'arrêt du serveur
@app.on_event("shutdown")
async def shutdown():
    await alert_routes.session.close()  # Ferme la session globale définie dans `alert_routes.py`


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9091)
