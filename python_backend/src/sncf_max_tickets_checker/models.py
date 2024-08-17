import uuid
from typing import Optional, List

from pydantic import BaseModel


class Alert(BaseModel):
    alert_id: str = str(uuid.uuid4())
    origine_iata: str
    destination_iata: str
    date: str
    train_no: Optional[str] = None
    heure_depart_debut: Optional[str] = None  # Heure de départ début (ex: 06:00)
    heure_depart_fin: Optional[str] = None  # Heure de départ fin (ex: 09:00)
    email: str


class Client(BaseModel):
    email: str
    client_id: str = str(uuid.uuid4())
    alerts: List[Alert] = []
