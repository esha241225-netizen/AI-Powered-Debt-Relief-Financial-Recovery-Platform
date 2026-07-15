import React, { useState, useEffect } from 'react';
import api, { setupAxiosInterceptors } from './api';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import FinancialHealth from './pages/FinancialHealth';
import SettlementPredictor from './pages/SettlementPredictor';
import NegotiationEmail from './pages/NegotiationEmail';
import KnowYourRights from './pages/KnowYourRights';
import History from './pages/History';

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [preselectedLoanId, setPreselectedLoanId] = useState(null);

  // Setup Axios global response interceptors on initial mount
  useEffect(() => {
    setupAxiosInterceptors(handleLogout);
  }, []);

  // Authenticate on startup if token exists
  useEffect(() => {
    if (token) {
      const savedUser = localStorage.getItem('user');
      if (savedUser) {
        setUser(JSON.parse(savedUser));
      } else {
        // Fetch profile using secure Axios client
        api.get('/auth/me')
          .then(res => {
            setUser(res.data.user);
            localStorage.setItem('user', JSON.stringify(res.data.user));
          })
          .catch(() => {
            handleLogout();
          });
      }
    }
  }, [token]);

  const handleLoginSuccess = (userData, accessToken) => {
    setUser(userData);
    setToken(accessToken);
    setActiveTab('dashboard');
  };

  const handleLogout = () => {
    setToken('');
    setUser(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  };

  const handleSelectLetter = (loanId) => {
    setPreselectedLoanId(loanId);
    setActiveTab('letters');
  };

  // If not logged in, render the Login/Register screens
  if (!token || !user) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div style={styles.appContainer}>
      {/* Sidebar navigation */}
      <aside style={styles.sidebar}>
        <div style={styles.logoArea}>
          <div style={styles.logoIcon}>🛡️</div>
          <div style={styles.logoText}>
            <div style={styles.mainLogoText}>FinRelief</div>
            <div style={styles.subLogoText}>AI Advisor</div>
          </div>
        </div>

        <nav style={styles.navMenu}>
          <button 
            onClick={() => setActiveTab('dashboard')}
            style={{ ...styles.navBtn, ...(activeTab === 'dashboard' ? styles.navBtnActive : {}) }}
          >
            📊 Dashboard
          </button>
          <button 
            onClick={() => setActiveTab('health')}
            style={{ ...styles.navBtn, ...(activeTab === 'health' ? styles.navBtnActive : {}) }}
          >
            💚 Financial Health
          </button>
          <button 
            onClick={() => setActiveTab('predictor')}
            style={{ ...styles.navBtn, ...(activeTab === 'predictor' ? styles.navBtnActive : {}) }}
          >
            🔮 Predictor
          </button>
          <button 
            onClick={() => {
              setActiveTab('letters');
              setPreselectedLoanId(null);
            }}
            style={{ ...styles.navBtn, ...(activeTab === 'letters' ? styles.navBtnActive : {}) }}
          >
            📄 Negotiation Email
          </button>
          <button 
            onClick={() => setActiveTab('rights')}
            style={{ ...styles.navBtn, ...(activeTab === 'rights' ? styles.navBtnActive : {}) }}
          >
            ⚖️ Know Your Rights
          </button>
          <button 
            onClick={() => setActiveTab('history')}
            style={{ ...styles.navBtn, ...(activeTab === 'history' ? styles.navBtnActive : {}) }}
          >
            🕒 History
          </button>
        </nav>

        {/* User Card & Logout */}
        <div style={styles.userCard}>
          <div style={styles.userInfo}>
            <div style={styles.userAvatar}>
              {user.name ? user.name.charAt(0).toUpperCase() : 'U'}
            </div>
            <div style={styles.userDetails}>
              <div style={styles.userName}>{user.name}</div>
              <div style={styles.userEmail}>{user.email}</div>
            </div>
          </div>
          <button onClick={handleLogout} style={styles.logoutBtn}>
            🚪 Sign Out
          </button>
        </div>
      </aside>

      {/* Main content display */}
      <main style={styles.mainContent}>
        {activeTab === 'dashboard' && <Dashboard token={token} user={user} />}
        {activeTab === 'health' && <FinancialHealth token={token} />}
        {activeTab === 'predictor' && <SettlementPredictor token={token} onSelectLetter={handleSelectLetter} />}
        {activeTab === 'letters' && <NegotiationEmail token={token} preselectedLoanId={preselectedLoanId} />}
        {activeTab === 'rights' && <KnowYourRights />}
        {activeTab === 'history' && <History token={token} />}
      </main>
    </div>
  );
}

const styles = {
  appContainer: {
    display: 'flex',
    minHeight: '100vh',
    width: '100vw',
    backgroundColor: 'var(--bg-base)',
    color: 'var(--text-primary)',
    overflow: 'hidden',
  },
  sidebar: {
    width: 'var(--sidebar-width)',
    backgroundColor: 'var(--bg-surface)',
    borderRight: '1px solid var(--border)',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
    padding: '2rem 1.5rem',
  },
  logoArea: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    marginBottom: '3rem',
  },
  logoIcon: {
    width: '2.5rem',
    height: '2.5rem',
    borderRadius: '0.5rem',
    backgroundColor: 'var(--accent-blue)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '1.25rem',
  },
  logoText: {
    display: 'flex',
    flexDirection: 'column',
  },
  mainLogoText: {
    fontWeight: '700',
    fontSize: '1.15rem',
    letterSpacing: '-0.02em',
    color: 'var(--text-primary)',
    fontFamily: 'var(--font-display)',
  },
  subLogoText: {
    fontSize: '0.75rem',
    color: 'var(--accent-blue-light)',
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  navMenu: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
    flex: 1,
  },
  navBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    padding: '0.85rem 1rem',
    borderRadius: 'var(--radius)',
    backgroundColor: 'transparent',
    border: 'none',
    color: 'var(--text-secondary)',
    fontSize: '0.95rem',
    fontWeight: '500',
    cursor: 'pointer',
    textAlign: 'left',
    transition: 'var(--transition-fast)',
    fontFamily: 'var(--font-body)',
  },
  navBtnActive: {
    backgroundColor: 'rgba(37, 99, 235, 0.08)',
    color: 'var(--accent-blue)',
    fontWeight: '600',
  },
  userCard: {
    borderTop: '1px solid var(--border)',
    paddingTop: '1.5rem',
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
  },
  userInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
  },
  userAvatar: {
    width: '2.25rem',
    height: '2.25rem',
    borderRadius: '50%',
    backgroundColor: 'var(--accent-blue)',
    color: '#ffffff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: '600',
    fontSize: '0.95rem',
  },
  userDetails: {
    overflow: 'hidden',
  },
  userName: {
    fontWeight: '600',
    fontSize: '0.9rem',
    color: 'var(--text-primary)',
  },
  userEmail: {
    fontSize: '0.75rem',
    color: 'var(--text-secondary)',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  logoutBtn: {
    padding: '0.6rem',
    borderRadius: 'var(--radius)',
    backgroundColor: 'rgba(239, 68, 68, 0.05)',
    color: 'var(--accent-red)',
    border: '1px solid rgba(239, 68, 68, 0.1)',
    cursor: 'pointer',
    fontSize: '0.85rem',
    fontWeight: '600',
    transition: 'all var(--transition-fast)',
    fontFamily: 'var(--font-body)',
  },
  mainContent: {
    flex: 1,
    height: '100vh',
    overflowY: 'auto',
    backgroundColor: 'var(--bg-base)',
  }
};
