function Header() {
    return (
        <header className="header">
            <div>
                <h1>SENTINEL-X</h1>
                <p>Centre de Commandement Tactique</p>
            </div>

            <div className="system-state">
                <span className="status-dot" />
                <span>SYSTÈME OPÉRATIONNEL</span>
            </div>
        </header>
    );
}

export default Header;