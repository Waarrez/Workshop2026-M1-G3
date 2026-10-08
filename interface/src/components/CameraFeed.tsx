const CAMERA_URL = `http://${window.location.hostname}:8001/camera/stream`;

function CameraFeed() {
    return (
        <div className="camera-feed">
            <img
                src={CAMERA_URL}
                className="camera-video"
                alt="Flux vidéo de la webcam USB"
            />

            <div className="camera-status">
                <span className="status-dot" />
                CAMÉRA ACTIVE
            </div>
        </div>
    );
}

export default CameraFeed;