import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Dashboard } from './pages/Dashboard';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app-container">
        <aside className="sidebar glass-panel">
          <div className="sidebar__logo">
            <div className="logo-icon">AG</div>
            <span className="logo-text">SalesAgent</span>
          </div>
          <nav className="sidebar__nav">
            <a href="/" className="nav-item active">Dashboard</a>
            <a href="/conversations" className="nav-item">Conversações</a>
            <a href="/leads" className="nav-item">Leads</a>
            <a href="/settings" className="nav-item">Configurações</a>
          </nav>
          <div className="sidebar__footer">
            <div className="user-profile">
              <div className="user-avatar">JD</div>
              <div className="user-info">
                <span className="user-name">João D.</span>
                <span className="user-role">Consultor</span>
              </div>
            </div>
          </div>
        </aside>
        
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            {/* Other routes can be added here */}
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
