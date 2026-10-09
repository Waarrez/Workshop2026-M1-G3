
import { useEffect, useState } from 'react';

const CAMERA_URL = '/camera/stream';
const HEALTH_URL = '/camera/health';

function CameraFeed() {
    const [serviceAvailable, setServiceAvailable] = useState(false);
    const [streamActive, setStreamActive] = useState(false);

    useEffect(() => {
        let cancelled = false;

        const checkCamera = async () => {
            try {
                const response = await fetch(HEALTH_URL, {
                    cache: 'no-store',
                });

                if (!response.ok) {
                    if (!cancelled) {
                        setServiceAvailable(false);
                        setStreamActive(false);
                    }

                    return;
                }

                if (!cancelled) {
                    setServiceAvailable(true);
                }
            } catch {
                if (!cancelled) {
                    setServiceAvailable(false);
                    setStreamActive(false);
                }
            }
        };

        void checkCamera();

        const interval = window.setInterval(() => {
            void checkCamera();
        }, 3000);

        return () => {
            cancelled = true;
            window.clearInterval(interval);
        };
    }, []);

    return (
        <div className="camera-feed">
            {serviceAvailable ? (
                <img
                    src={CAMERA_URL}
                    className="camera-video"
                    alt="Flux vidéo de la webcam USB"
                    onLoad={() => setStreamActive(true)}
                    onError={() => setStreamActive(false)}
                />
            ) : (
                <div className="camera-placeholder">
                    <div className="camera-icon">CAM</div>
                    <span>CAMÉRA INACTIVE</span>
                    <small>Serveur vidéo indisponible</small>
                </div>
            )}

            <div className="camera-status">
                <span
                    className={`status-dot ${
                        streamActive ? 'status-ok' : 'status-warning'
                    }`}
                />
                {streamActive
                    ? 'CAMÉRA ACTIVE'
                    : serviceAvailable
                      ? 'FLUX VIDÉO INDISPONIBLE'
                      : 'CAMÉRA INACTIVE'}
            </div>
        </div>
    );
}

export default CameraFeed;