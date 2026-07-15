import React, { useState } from 'react';
import api from '../api';

export default function Login({ onLoginSuccess }) {
  const [isRegister, setIsRegister] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('kumaraskash02401@gmail.com');
  const [password, setPassword] = useState('123456');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const url = isRegister ? '/auth/register' : '/auth/login';
    const payload = isRegister ? { name, email, password } : { email, password };

    try {
      // Use Axios API instance
      const response = await api.post(url, payload);
      const data = response.data;

      // Save token and user details to localStorage
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));

      onLoginSuccess(data.user, data.access_token);
    } catch (err) {
      const errMsg = err.response?.data?.detail || err.message || 'Authentication failed';
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      {/* Left panel: Promotional branding */}
      <div style={styles.leftPanel}>
        <div style={styles.logoRow}>
          <div style={styles.logoIcon}>
            <span style={{ fontSize: '1.25rem' }}>🛡️</span>
          </div>
          <span style={styles.logoText}>FinRelief AI</span>
        </div>

        <div style={styles.heroContent}>
          <h1 style={styles.heroHeading}>
            Take Control of Your <span style={styles.glowText}>Financial Future</span>
          </h1>
          <p style={styles.heroSubheading}>
            AI-powered debt management that helps you negotiate smarter, settle faster, and live debt-free sooner.
          </p>
        </div>

        <div style={styles.badgeRow}>
          <div style={styles.badge}>
            <div style={styles.badgeValue}>40-75%</div>
            <div style={styles.badgeLabel}>Settlement Range</div>
          </div>
          <div style={styles.badge}>
            <div style={styles.badgeValue}>AI</div>
            <div style={styles.badgeLabel}>Powered Strategy</div>
          </div>
          <div style={styles.badge}>
            <div style={styles.badgeValue}>Free</div>
            <div style={styles.badgeLabel}>To Get Started</div>
          </div>
        </div>
      </div>

      {/* Right panel: Login / Register Form */}
      <div style={styles.rightPanel}>
        <div style={styles.formCard}>
          <h2 style={styles.formTitle}>Welcome back</h2>
          <p style={styles.formSubtitle}>Sign in to your dashboard</p>

          {/* Toggle buttons */}
          <div style={styles.toggleContainer}>
            <button 
              type="button" 
              onClick={() => setIsRegister(false)}
              style={{
                ...styles.toggleBtn,
                ...(isRegister ? {} : styles.toggleBtnActive)
              }}
            >
              Sign In
            </button>
            <button 
              type="button" 
              onClick={() => setIsRegister(true)}
              style={{
                ...styles.toggleBtn,
                ...(isRegister ? styles.toggleBtnActive : {})
              }}
            >
              Register
            </button>
          </div>

          {error && <div style={styles.errorAlert}>{error}</div>}

          <form onSubmit={handleSubmit} style={styles.form}>
            {isRegister && (
              <div style={styles.formGroup}>
                <label style={styles.label}>Full Name</label>
                <input 
                  type="text" 
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="John Doe"
                  required
                  style={styles.input}
                />
              </div>
            )}

            <div style={styles.formGroup}>
              <label style={styles.label}>Email address</label>
              <input 
                type="email" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
                style={styles.input}
              />
            </div>

            <div style={styles.formGroup}>
              <label style={styles.label}>Password</label>
              <input 
                type="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                style={styles.input}
              />
            </div>

            <button 
              type="submit" 
              disabled={loading}
              style={styles.submitBtn}
            >
              {loading ? 'Processing...' : (isRegister ? 'Register →' : 'Sign In →')}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

const styles = {
  container: {
    display: 'flex',
    minHeight: '100vh',
    width: '100vw',
    backgroundColor: 'var(--bg-base)',
    color: 'var(--text-primary)',
    fontFamily: 'var(--font-body)',
  },
  leftPanel: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
    padding: '3rem 4rem',
    background: 'radial-gradient(circle at 10% 20%, rgba(37, 99, 235, 0.08) 0%, transparent 60%), radial-gradient(circle at 80% 80%, rgba(16, 185, 129, 0.06) 0%, transparent 50%)',
    borderRight: '1px solid var(--border)',
  },
  logoRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
  },
  logoIcon: {
    width: '2.5rem',
    height: '2.5rem',
    borderRadius: '0.5rem',
    backgroundColor: 'var(--accent-blue)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoText: {
    fontSize: '1.25rem',
    fontWeight: 'bold',
    letterSpacing: '-0.025em',
  },
  heroContent: {
    maxWidth: '32rem',
    margin: 'auto 0',
  },
  heroHeading: {
    fontSize: '3rem',
    fontWeight: '800',
    lineHeight: '1.15',
    marginBottom: '1.5rem',
    fontFamily: 'var(--font-display)',
    letterSpacing: '-0.03em',
  },
  glowText: {
    background: 'linear-gradient(135deg, var(--accent-blue) 0%, var(--accent-green) 100%)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  },
  heroSubheading: {
    fontSize: '1.1rem',
    lineHeight: '1.6',
    color: 'var(--text-secondary)',
  },
  badgeRow: {
    display: 'flex',
    gap: '1.5rem',
  },
  badge: {
    flex: 1,
    padding: '1.25rem',
    borderRadius: 'var(--radius)',
    backgroundColor: 'rgba(255, 255, 255, 0.02)',
    border: '1px solid var(--border)',
  },
  badgeValue: {
    fontSize: '1.5rem',
    fontWeight: '700',
    color: 'var(--accent-blue-light)',
    marginBottom: '0.25rem',
    fontFamily: 'var(--font-display)',
  },
  badgeLabel: {
    fontSize: '0.85rem',
    color: 'var(--text-secondary)',
  },
  rightPanel: {
    width: '45%',
    minWidth: '28rem',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'var(--bg-surface)',
    padding: '3rem',
  },
  formCard: {
    width: '100%',
    maxWidth: '24rem',
  },
  formTitle: {
    fontSize: '2rem',
    fontWeight: '700',
    marginBottom: '0.5rem',
    fontFamily: 'var(--font-display)',
    letterSpacing: '-0.02em',
  },
  formSubtitle: {
    color: 'var(--text-secondary)',
    marginBottom: '2rem',
    fontSize: '0.95rem',
  },
  toggleContainer: {
    display: 'flex',
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    borderRadius: 'var(--radius)',
    padding: '0.25rem',
    marginBottom: '2rem',
    border: '1px solid var(--border)',
  },
  toggleBtn: {
    flex: 1,
    padding: '0.6rem',
    borderRadius: 'var(--radius)',
    backgroundColor: 'transparent',
    border: 'none',
    color: 'var(--text-secondary)',
    cursor: 'pointer',
    fontSize: '0.9rem',
    fontWeight: '500',
    transition: 'all var(--transition-fast)',
    fontFamily: 'var(--font-body)',
  },
  toggleBtnActive: {
    backgroundColor: 'var(--accent-blue)',
    color: '#ffffff',
    boxShadow: '0 4px 12px rgba(37, 99, 235, 0.2)',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1.25rem',
  },
  formGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
  },
  label: {
    fontSize: '0.85rem',
    fontWeight: '500',
    color: 'var(--text-primary)',
  },
  input: {
    padding: '0.85rem 1rem',
    borderRadius: 'var(--radius)',
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    border: '1px solid var(--border)',
    color: 'var(--text-primary)',
    fontSize: '0.95rem',
    outline: 'none',
    transition: 'border-color var(--transition-fast), box-shadow var(--transition-fast)',
    fontFamily: 'var(--font-body)',
  },
  submitBtn: {
    marginTop: '0.75rem',
    padding: '0.85rem',
    borderRadius: 'var(--radius)',
    backgroundColor: 'var(--accent-blue)',
    color: '#ffffff',
    fontSize: '0.95rem',
    fontWeight: '600',
    border: 'none',
    cursor: 'pointer',
    transition: 'all var(--transition-fast)',
    boxShadow: '0 4px 14px rgba(37, 99, 235, 0.3)',
    fontFamily: 'var(--font-body)',
  },
  errorAlert: {
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid rgba(239, 68, 68, 0.2)',
    color: 'var(--accent-red)',
    padding: '0.75rem 1rem',
    borderRadius: 'var(--radius)',
    fontSize: '0.9rem',
    marginBottom: '1.25rem',
  }
};
