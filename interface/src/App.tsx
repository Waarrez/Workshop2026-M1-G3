
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

const API_URL = '';
const WS_PROTOCOL =
    window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const WS_URL = `${WS_PROTOCOL}//${window.location.host}/ws`;
const MAX_READINGS = 30;
const MAX_EVENTS = 100;

function App() {
    const [isLightTheme, setIsLightTheme] = useState(() => {
        return localStorage.getItem('sentinel-theme') === 'light';
    });

    const [readings, setReadings] = useState<Reading[]>([]);
    const [devices, setDevices] = useState<Device[]>([]);
    const [events, setEvents] = useState<Event[]>([]);

    useEffect(() => {
        document.documentElement.dataset.theme =
            isLightTheme ? 'light' : 'dark';

        localStorage.setItem(
            'sentinel-theme',
            isLightTheme ? 'light' : 'dark',
        );
    }, [isLightTheme]);

    useEffect(() => {
        let cancelled = false;

        const loadHistory = async () => {
            try {
                const [readingsResponse, eventsResponse] =
                    await Promise.all([
                        fetch(
                            `${API_URL}/api/readings?limit=${MAX_READINGS}`,
                        ),
                        fetch(
                            `${API_URL}/api/events?limit=${MAX_EVENTS}`,
                        ),
                    ]);

                if (!readingsResponse.ok) {
                    throw new Error(
                        `Historique des mesures : HTTP ${readingsResponse.status}`,
                    );
                }

                const history =
                    (await readingsResponse.json()) as Reading[];

                if (cancelled) {
                    return;
                }

                setReadings(history.slice(-MAX_READINGS));

                setDevices(
                    history.reduce<Device[]>((current, reading) => {
                        const existingDevice = current.find(
                            (device) => device.id === reading.id,
                        );

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

                if (eventsResponse.ok) {
                    const historyEvents =
                        (await eventsResponse.json()) as Event[];

                    if (!cancelled) {
                        setEvents(historyEvents.slice(-MAX_EVENTS));
                    }
                } else {
                    console.error(
                        'Impossible de récupérer l’historique des événements :',
                        `HTTP ${eventsResponse.status}`,
                    );
                }
            } catch (error) {
                if (!cancelled) {
                    console.error(
                        'Impossible de récupérer les données initiales :',
                        error,
                    );
                }
            }
        };

        void loadHistory();

        return () => {
            cancelled = true;
        };
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
                    const data = JSON.parse(
                        message.data,
                    ) as WebSocketMessage;

                    if (data.type === 'reading') {
                        const reading = data.payload as Reading;

                        setReadings((current) =>
                            [...current, reading].slice(-MAX_READINGS),
                        );

                        setDevices((current) => {
                            const existingDevice = current.find(
                                (device) => device.id === reading.id,
                            );

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
                                          last_seen: reading.received_at,
                                          online: true,
                                      }
                                    : device,
                            );
                        });
                    }

                    if (data.type === 'event') {
                        const event = data.payload as Event;

                        setEvents((current) =>
                            [...current, event].slice(-MAX_EVENTS),
                        );
                    }
                } catch (error) {
                    console.error(
                        'Message WebSocket invalide :',
                        error,
                    );
                }
            };

            websocket.onerror = () => {
                console.error('Erreur WebSocket.');
            };

            websocket.onclose = () => {
                if (cancelled) {
                    return;
                }

                console.info(
                    'WebSocket déconnecté. Nouvelle tentative dans 3 secondes.',
                );

                reconnectTimeout = window.setTimeout(
                    connectWebSocket,
                    3000,
                );
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