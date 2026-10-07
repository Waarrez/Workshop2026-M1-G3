interface HeaderProps {
    isLightTheme: boolean;
    onToggleTheme: () => void;
}

function Header({ isLightTheme, onToggleTheme }: HeaderProps) {
return (
        <header className="header">
            <div>
                <h1>SENTINEL-X</h1>
                <p>Centre de Commandement Tactique</p>
            </div>

            <div className="header-actions">
                <div className="system-state">
                    <span className="status-dot" />
                    <span>SYSTÈME OPÉRATIONNEL</span>
                </div>

                <button
                    className="theme-toggle"
                    type="button"
                    onClick={onToggleTheme}
                    aria-label={`Activer le thème ${isLightTheme ? 'sombre' : 'clair'}`}
                >
                    {isLightTheme ? '☾ Sombre' : '☀ Clair'}
                </button>
            </div>
        </header>
    );
}

export default Header;
