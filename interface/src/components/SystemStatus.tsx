import { useState } from 'react';
import type { Device, Event, Reading } from '../types';

interface SystemStatusProps {
    devices: Device[];
    readings: Reading[];
    events: Event[];
}

function SystemStatus({
    devices,
    readings,
    events,
}: SystemStatusProps) {
    const [buzzerLoading, setBuzzerLoading] = useState(false);

    const onlineDevices = devices.filter(
        (device) => device.online,
    ).length;

    const latestReading = readings.at(-1);

    const sensorCount = [
        latestReading?.temp_c,
        latestReading?.humidity_pct,
        latestReading?.gas_raw,
        latestReading?.motion,
    ].filter(
        (value) => value !== null && value !== undefined,
    ).length;

    const sensorTotal = 4;

    const triggerBuzzer = async () => {
        if (!latestReading || buzzerLoading) {
            return;
        }

        setBuzzerLoading(true);

        try {
            const response = await fetch('/api/commands', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    device_id: latestReading.id,
                    target: 'buzzer',
                    state: true,
                    duration_ms: 3000,
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            console.error(
                'Impossible de déclencher le buzzer :',
                error,
            );
        } finally {
            setBuzzerLoading(false);
        }
    };

    return (
        <div className="status-grid">
            <div className="status-card">
                <span className="status-label">Edge Node</span>
                <strong>
                    {onlineDevices > 0 ? 'ONLINE' : 'OFFLINE'}
                </strong>
                <span
                    className={
                        onlineDevices > 0
                            ? 'status-ok'
                            : 'status-warning'
                    }
                >
                    {onlineDevices > 0
                        ? 'Opérationnel'
                        : 'Hors ligne'}
                </span>
            </div>

            <div className="status-card">
                <span className="status-label">Réseau</span>
                <strong>
                    {onlineDevices > 0
                        ? 'CONNECTÉ'
                        : 'DÉCONNECTÉ'}
                </strong>
                <span
                    className={
                        onlineDevices > 0
                            ? 'status-ok'
                            : 'status-warning'
                    }
                >
                    {onlineDevices > 0
                        ? 'Communication active'
                        : 'Communication interrompue'}
                </span>
            </div>

            <div className="status-card">
                <span className="status-label">Capteurs</span>
                <strong>
                    {sensorCount} / {sensorTotal}
                </strong>
                <span
                    className={
                        sensorCount === sensorTotal
                            ? 'status-ok'
                            : 'status-warning'
                    }
                >
                    {sensorCount === sensorTotal
                        ? 'Tous opérationnels'
                        : 'Vérification nécessaire'}
                </span>
            </div>

            <div className="status-card">
                <span className="status-label">Alertes</span>
                <strong>{events.length}</strong>
                <span
                    className={
                        events.length === 0
                            ? 'status-ok'
                            : 'status-warning'
                    }
                >
                    {events.length === 0
                        ? 'Aucune menace'
                        : 'Événement(s) détecté(s)'}
                </span>
            </div>

            <div className="status-card">
                <span className="status-label">Buzzer</span>

                <button
                    type="button"
                    className="buzzer-button"
                    onClick={triggerBuzzer}
                    disabled={!latestReading || buzzerLoading}
                >
                    {buzzerLoading
                        ? 'ACTIVATION...'
                        : 'FAIRE SONNER'}
                </button>

                <span className="status-ok">
                    {latestReading
                        ? 'Commande disponible'
                        : 'Edge Node indisponible'}
                </span>
            </div>
        </div>
    );
}

export default SystemStatus;