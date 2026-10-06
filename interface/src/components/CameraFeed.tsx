function CameraFeed() {
    return (
        <div className="camera-feed">
            <div className="camera-placeholder">
                <div className="camera-icon">◉</div>
                <span>WEBCAM USB</span>
                <small>Flux vidéo en attente</small>
            </div>

            <div className="camera-status">
                <span className="status-dot" />
                CAMÉRA ACTIVE
            </div>
        </div>
    );
}

export default CameraFeed;