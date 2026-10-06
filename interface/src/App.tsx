import CameraFeed from './components/CameraFeed';
import EnvironmentChart from './components/EnvironmentChart';
import Header from './components/Header';
import SystemStatus from './components/SystemStatus';
import './index.css';

function App() {
    return (
        <div className="app">
            <Header />

            <main className="dashboard">
                <section className="dashboard-section">
                    <div className="section-title">
                        <h2>Supervision</h2>
                        <span className="live-indicator">LIVE</span>
                    </div>

                    <SystemStatus />
                </section>

                <section className="dashboard-grid">
                    <div className="panel camera-panel">
                        <h2>Surveillance vidéo</h2>
                        <CameraFeed />
                    </div>

                    <div className="panel environment-panel">
                        <h2>Données environnementales</h2>
                        <EnvironmentChart />
                    </div>
                </section>
            </main>
        </div>
    );
}

export default App;