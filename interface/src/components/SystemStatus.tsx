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
    const onlineDevices = devices.filter(
        (device) => device.online,
    ).length;

    const latestReading = readings.at(-1);

    const sensorCount = [
        latestReading?.temp_c,
        latestReading?.humidity_pct,
        latestReading?.gas_raw,
        latestReading?.motion,
    ].filter((value) => value !== null && value !== undefined).length;

    const sensorTotal = 4;

    return (
        <div className="status-grid">
            <div className="status-card">
                <span className="status-label">Edge Node</span>
                <strong>{onlineDevices > 0 ? 'ONLINE' : 'OFFLINE'}</strong>
                <span className={onlineDevices > 0 ? 'status-ok' : 'status-warning'}>{onlineDevices > 0 ? 'Opérationnel' : 'Hors ligne'}</span>
            </div>

            <div className="status-card">
                <span className="status-label">Réseau</span>
                <strong>{onlineDevices > 0 ? 'CONNECTÉ' : 'DÉCONNECTÉ'}</strong>
                <span className={onlineDevices > 0 ? 'status-ok' : 'status-warning'}>{onlineDevices > 0 ? 'Communication active' : 'Communication interrompue'}</span>
            </div>

            <div className="status-card">
                <span className="status-label">Capteurs</span>
                <strong>{sensorCount} / {sensorTotal}</strong>
                <span className={sensorCount === sensorTotal ? 'status-ok' : 'status-warning'}>{sensorCount === sensorTotal ? 'Tous opérationnels' : 'Vérification nécessaire'}</span>
            </div>

            <div className="status-card">
                <span className="status-label">Alertes</span>
                <strong>{events.length}</strong>
                <span className={events.length === 0 ? 'status-ok' : 'status-warning'}>{events.length === 0 ? 'Aucune menace' : 'Événement(s) détecté(s)'}</span>
            </div>
        </div>
    );
}

export default SystemStatus;