function SystemStatus() {
    return (
        <div className="status-grid">
            <div className="status-card">
                <span className="status-label">Edge Node</span>
                <strong>ONLINE</strong>
                <span className="status-ok">Opérationnel</span>
            </div>

            <div className="status-card">
                <span className="status-label">Réseau</span>
                <strong>CONNECTÉ</strong>
                <span className="status-ok">Communication active</span>
            </div>

            <div className="status-card">
                <span className="status-label">Capteurs</span>
                <strong>4 / 4</strong>
                <span className="status-ok">Tous opérationnels</span>
            </div>

            <div className="status-card">
                <span className="status-label">Alertes</span>
                <strong>0</strong>
                <span className="status-ok">Aucune menace</span>
            </div>
        </div>
    );
}

export default SystemStatus;