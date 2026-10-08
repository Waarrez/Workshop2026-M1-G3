import { useEffect, useState } from 'react';

const CAMERA_URL = `http://${window.location.hostname}:8001/camera/stream`;
const HEALTH_URL = `http://${window.location.hostname}:8001/health`;

function CameraFeed() {
    const [cameraActive, setCameraActive] = useState(false);

    useEffect(() => {
        const checkCamera = async () => {
            try {
                const response = await fetch(HEALTH_URL);

                if (!response.ok) {
                    setCameraActive(false);
                    return;
                }

                const data = await response.json();

                setCameraActive(data.camera_open === true);
            } catch {
                setCameraActive(false);
            }
        };

        checkCamera();

        const interval = window.setInterval(checkCamera, 3000);

        return () => window.clearInterval(interval);
    }, []);

    return (
        <div className="camera-feed">
            {cameraActive ? (
                <img
                    src={CAMERA_URL}
                    className="camera-video"
                    alt="Flux vidéo de la webcam USB"
                    onError={() => setCameraActive(false)}
                />
            ) : (
                <div className="camera-placeholder">
                    <div className="camera-icon">CAM</div>
                    <span>CAMÉRA INACTIVE</span>
                    <small>Webcam indisponible</small>
                </div>
            )}

            <div className="camera-status">
                <span className="status-dot" />
                {cameraActive ? 'CAMÉRA ACTIVE' : 'CAMÉRA INACTIVE'}
            </div>
        </div>
    );
}

export default CameraFeed;