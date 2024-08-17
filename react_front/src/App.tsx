import React, {useState} from 'react'
import './style/App.scss'

interface Alert {
    alert_id: string
    origine_iata: string
    destination_iata: string
    date: string
    train_no: string | null
    heure_depart_debut: string | null
    heure_depart_fin: string | null
    email: string
}

function App() {
    const [apiUrl] = useState(import.meta.env.VITE_API_URL)
    const [email, setEmail] = useState('')
    const [authenticated, setAuthenticated] = useState(false)
    const [alerts, setAlerts] = useState<Alert[]>([])
    const [origine_iata, setOrigineIata] = useState('')
    const [destination_iata, setDestinationIata] = useState('')
    const [date, setDate] = useState('')
    const [train_no, setTrainNo] = useState('')
    const [heure_depart_debut, setHeureDepartDebut] = useState('')
    const [heure_depart_fin, setHeureDepartFin] = useState('')

    async function createAlert(e: React.FormEvent) {
        e.preventDefault()
        const response = await fetch(`${apiUrl}/alerts`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                origine_iata,
                destination_iata,
                date,
                train_no,
                heure_depart_debut,
                heure_depart_fin,
                email
            })
        })
        const data = await response.json()
        if (response.ok) {
            setAlerts([...alerts, data])
        }
        await getAlerts()
    }

    async function getAlerts() {
        const response = await fetch(`${apiUrl}/alerts/?email=${email}`)
        const data = await response.json()

        try {
            if (typeof data === 'object' && data.length > 0) {
                setAlerts(data)
                setAuthenticated(true)
            } else {
                console.error('Error:', data)
            }
        } catch (error) {
            console.error('Error:', error)
        }
    }

    async function getProfile(e: React.FormEvent) {
        e.preventDefault()
        await getAlerts()
    }

    return (
        <div>
            {!authenticated && (
                <>
                    <h1>Alertes MAX SNCF</h1>
                    <form className="form mail_auth" onSubmit={getProfile}>
                        <div className={"input_box"}>
                            <label htmlFor="email">Votre Email :</label>
                            <input type="email" id="email" name="email" onChange={(e) => setEmail(e.target.value)}
                                   value={email} required/>
                        </div>
                        <button type="submit">Accéder à mes alertes</button>
                    </form>
                </>
            )}

            {authenticated && (
                <>
                    <h1>Alertes MAX SNCF</h1>
                    <h2>S'abonner à une alerte</h2>
                    <form className="form" onSubmit={createAlert}>
                        <div className={"input_box"}>
                            <label htmlFor="gare">Gare départ :</label>
                            <input type="text" id="gare" name="origine_iata"
                                   onChange={(e) => setOrigineIata(e.target.value)}
                                   value={origine_iata} required/>
                        </div>
                        <div className={"input_box"}>
                            <label htmlFor="gare">Gare arrivée :</label>
                            <input type="text" id="gare" name="destination_iata"
                                   onChange={(e) => setDestinationIata(e.target.value)}
                                   value={destination_iata} required/>
                        </div>
                        <div className={"input_box"}>
                            <label htmlFor="date">Date :</label>
                            <input type="date" id="date" name="date" onChange={(e) => setDate(e.target.value)}
                                   value={date} required/>
                        </div>
                        <div className={"input_box"}>
                            <label htmlFor="train_no">Numéro de train :</label>
                            <input type="text" id="train_no" name="train_no"
                                   onChange={(e) => setTrainNo(e.target.value)}
                                   value={train_no} required/>
                        </div>
                        <div className={"input_box"}>
                            <label htmlFor="heure_depart_debut">Heure de départ début :</label>
                            <input type="time" id="heure_depart_debut" name="heure_depart_debut"
                                   onChange={(e) => setHeureDepartDebut(e.target.value)}
                                   value={heure_depart_debut} required/>
                        </div>
                        <div className={"input_box"}>
                            <label htmlFor="heure_depart_fin">Heure de départ fin :</label>
                            <input type="time" id="heure_depart_fin" name="heure_depart_fin"
                                   onChange={(e) => setHeureDepartFin(e.target.value)}
                                   value={heure_depart_fin} required/>
                        </div>
                        <button type="submit">S'abonner</button>
                    </form>

                    <h2>Mes alertes</h2>
                    <div className="alerts">
                        {alerts.map((alert: Alert) => (
                            <div className="alert" key={alert.alert_id}>
                                <div className="alert_info">
                                    <span>{alert.origine_iata}</span>
                                    <span>{alert.destination_iata}</span>
                                    <span>{alert.date}</span>
                                    <span>{alert.train_no}</span>
                                    <span>{alert.heure_depart_debut} - {alert.heure_depart_fin}</span>
                                </div>
                                <div className="alert_actions">
                                    <button>Modifier</button>
                                    <button>Supprimer</button>
                                </div>
                            </div>
                        ))}
                    </div>
                </>
            )}

        </div>
    )
}

export default App
