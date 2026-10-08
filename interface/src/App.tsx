import { useEffect, useState } from 'react';
import CameraFeed from './components/CameraFeed';
import EnvironmentChart from './components/EnvironmentChart';
import Header from './components/Header';
import SystemStatus from './components/SystemStatus';
import type {
    Device,
    Event,
    Reading,
    WebSocketMessage,
} from './types';
import './index.css';

const API_URL = `http://${window.location.hostname}:8000`;
const WS_URL = `ws://${window.location.hostname}:8000/ws`;
const MAX_READINGS = 30;

function App() {
    const [isLightTheme, setIsLightTheme] = useState(() => {
        return localStorage.getItem('sentinel-theme') === 'light';
    });

    const [readings, setReadings] = useState<Reading[]>([]);
    const [devices, setDevices] = useState<Device[]>([]);
    const [events, setEvents] = useState<Event[]>([]);

    useEffect(() => {
        document.documentElement.dataset.theme = isLightTheme ? 'light' : 'dark';
        localStorage.setItem('sentinel-theme', isLightTheme ? 'light' : 'dark');
    }, [isLightTheme]);

    useEffect(() => {
        const loadHistory = async () => {
            try {
                const response = await fetch(`${API_URL}/api/readings?limit=${MAX_READINGS}`);

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const history = (await response.json()) as Reading[];

                setReadings(history.slice(-MAX_READINGS));

                setDevices(
                    history.reduce<Device[]>((current, reading) => {
                        const existingDevice = current.find((device) => device.id === reading.id);

                        if (existingDevice) {
                            return current.map((device) =>
                                device.id === reading.id
                                    ? {
                                          ...device,
                                          last_seen: reading.received_at,
                                          online: true,
                                      }
                                    : device,
                            );
                        }

                        return [
                            ...current,
                            {
                                id: reading.id,
                                last_seen: reading.received_at,
                                online: true,
                            },
                        ];
                    }, []),
                );
            } catch (error) {
                console.error('Impossible de récupérer l’historique :', error);
            }
        };

        loadHistory();
    }, []);

    useEffect(() => {
        let websocket: WebSocket | null = null;
        let reconnectTimeout: number | undefined;
        let cancelled = false;

        const connectWebSocket = () => {
            if (cancelled) {
                return;
            }

            websocket = new WebSocket(WS_URL);

            websocket.onopen = () => {
                console.info('WebSocket connecté.');
            };

            websocket.onmessage = (message) => {
                try {
                    const data = JSON.parse(message.data) as WebSocketMessage;

                    if (data.type === 'reading') {
                        const reading = data.payload as Reading;

                        setReadings((current) => [...current, reading].slice(-MAX_READINGS));

                        setDevices((current) => {
                            const existingDevice = current.find((device) => device.id === reading.id);

                            if (!existingDevice) {
                                return [
                                    ...current,
                                    {
                                        id: reading.id,
                                        last_seen: reading.received_at,
                                        online: true,
                                    },
                                ];
                            }

                            return current.map((device) =>
                                device.id === reading.id
                                    ? {
                                          ...device,
                                          last_seen:
                                              reading.received_at,
                                          online: true,
                                      }
                                    : device,
                            );
                        });
                    }

                    if (data.type === 'event') {
                        const event = data.payload as Event;

                        setEvents((current) => [...current, event].slice(-100));
                    }
                } catch (error) {
                    console.error('Message WebSocket invalide :', error);
                }
            };

            websocket.onerror = () => {
                console.error('Erreur WebSocket.');
            };

            websocket.onclose = () => {
                if (cancelled) {
                    return;
                }

                console.info('WebSocket déconnecté. Nouvelle tentative dans 3 secondes.');

                reconnectTimeout = window.setTimeout(connectWebSocket, 3000);
            };
        };

        connectWebSocket();

        return () => {
            cancelled = true;

            if (reconnectTimeout !== undefined) {
                window.clearTimeout(reconnectTimeout);
            }

            websocket?.close();
        };
    }, []);

    return (
        <div className="app">
            <Header
                isLightTheme={isLightTheme}
                onToggleTheme={() =>
                    setIsLightTheme((current) => !current)
                }
            />

            <main className="dashboard">
                <section className="dashboard-section">
                    <div className="section-title">
                        <h2>Supervision</h2>
                        <span className="live-indicator">LIVE</span>
                    </div>

                    <SystemStatus
                        devices={devices}
                        readings={readings}
                        events={events}
                    />
                </section>

                <section className="dashboard-grid">
                    <div className="panel camera-panel">
                        <h2>Surveillance vidéo</h2>
                        <CameraFeed />
                    </div>

                    <div className="panel environment-panel">
                        <h2>Données environnementales</h2>
                        <EnvironmentChart readings={readings} />
                    </div>
                </section>
            </main>
        </div>
    );
}

export default App;
