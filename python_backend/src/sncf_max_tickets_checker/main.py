from fastapi import FastAPI

from sncf_max_tickets_checker.routes import alert_routes

app = FastAPI()

# Enregistrement des routes
app.include_router(alert_routes.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9091)


# Ajout d'un événement pour fermer proprement la session HTTP à l'arrêt du serveur
@app.on_event("shutdown")
async def shutdown():
    await alert_routes.session.close()  # Ferme la session globale définie dans `alert_routes.py`
