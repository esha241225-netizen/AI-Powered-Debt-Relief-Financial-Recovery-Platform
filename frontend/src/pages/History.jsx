import React, { useState, useEffect } from 'react';
import api from '../api';

export default function History({ token }) {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedLog, setSelectedLog] = useState(null);

  const fetchHistory = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await api.get('/ai-history');
      setLogs(response.data);
      if (response.data.length > 0) {
        setSelectedLog(response.data[0]);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load AI history logs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [token]);

  if (loading) {
    return <div style={styles.loadingContainer}>Loading AI session logs...</div>;
  }

  return (
    <div style={styles.container}>
      <div>
        <h1 style={styles.title}>History</h1>
        <p style={styles.subtitle}>Review and audit past AI outputs, settlement strategies, and correspondence.</p>
      </div>

      {error && <div style={styles.errorAlert}>{error}</div>}

      {logs.length === 0 ? (
        <div style={styles.emptyState}>
          <p>No past AI history records found. Start using AI advisors to generate logs.</p>
        </div>
      ) : (
        <div style={styles.workspace}>
          {/* History timeline list */}
          <div style={styles.sidebar}>
            <h3 style={styles.sidebarTitle}>Session Logs</h3>
            <div style={styles.logList}>
              {logs.map((log) => {
                const date = new Date(log.generated_at);
                const dateStr = date.toLocaleDateString('en-IN', {
                  day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit'
                });
                return (
                  <button
                    key={log.history_id}
                    onClick={() => setSelectedLog(log)}
                    style={{
                      ...styles.logBtn,
                      ...(selectedLog?.history_id === log.history_id ? styles.logBtnActive : {})
                    }}
                  >
                    <div style={styles.logMeta}>
                      <span>📅 {dateStr}</span>
                      <span>ID: #{log.history_id}</span>
                    </div>
                    <div style={styles.logSummary} title={log.ai_response}>
                      {log.ai_response || 'Negotiation strategy generation'}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Details Viewer */}
          {selectedLog && (
            <div style={styles.viewer}>
              <div style={styles.logTitleBar}>
                <h3>Session Details — Log #{selectedLog.history_id}</h3>
                <span style={styles.logDate}>
                  Generated: {new Date(selectedLog.generated_at).toLocaleString('en-IN')}
                </span>
              </div>

              {/* Strategy Output */}
              {selectedLog.negotiation_strategy && (
                <div style={styles.detailCard}>
                  <h4 style={styles.cardSectionTitle}>💼 Personalised Negotiation Strategy</h4>
                  <div style={styles.strategyBody}>
                    {selectedLog.negotiation_strategy}
                  </div>
                </div>
              )}

              {/* Settlement Letter Output */}
              {selectedLog.settlement_letter && (
                <div style={styles.detailCard}>
                  <h4 style={styles.cardSectionTitle}>📄 Generated Settlement Letter</h4>
                  <pre style={styles.letterPreview}>
                    {selectedLog.settlement_letter}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

const styles = {
  container: {
    padding: '2rem',
    display: 'flex',
    flexDirection: 'column',
    gap: '2rem',
    width: '100%',
  },
  loadingContainer: {
    color: 'var(--text-secondary)',
    fontSize: '1.1rem',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '400px',
  },
  title: {
    fontSize: '2rem',
    fontWeight: '700',
    letterSpacing: '-0.02em',
    fontFamily: 'var(--font-display)',
  },
  subtitle: {
    color: 'var(--text-secondary)',
    marginTop: '0.25rem',
  },
  workspace: {
    display: 'grid',
    gridTemplateColumns: '1.2fr 3fr',
    gap: '2rem',
    alignItems: 'start',
  },
  sidebar: {
    backgroundColor: 'var(--bg-surface)',
    borderRadius: 'var(--radius-lg)',
    border: '1px solid var(--border)',
    padding: '1.25rem',
  },
  sidebarTitle: {
    fontSize: '1rem',
    fontWeight: '600',
    marginBottom: '1rem',
    color: 'var(--text-secondary)',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  logList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.75rem',
  },
  logBtn: {
    padding: '1rem',
    borderRadius: 'var(--radius)',
    backgroundColor: 'rgba(255, 255, 255, 0.02)',
    border: '1px solid rgba(255, 255, 255, 0.04)',
    color: 'var(--text-primary)',
    cursor: 'pointer',
    textAlign: 'left',
    transition: 'all var(--transition-fast)',
    fontFamily: 'var(--font-body)',
  },
  logBtnActive: {
    backgroundColor: 'rgba(37, 99, 235, 0.1)',
    borderColor: 'var(--accent-blue)',
    color: '#ffffff',
  },
  logMeta: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '0.75rem',
    color: 'var(--text-secondary)',
    marginBottom: '0.35rem',
  },
  logSummary: {
    fontSize: '0.9rem',
    fontWeight: '500',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  viewer: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1.5rem',
  },
  logTitleBar: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottom: '1px solid var(--border)',
    paddingBottom: '0.75rem',
  },
  logDate: {
    fontSize: '0.85rem',
    color: 'var(--text-secondary)',
  },
  detailCard: {
    padding: '1.5rem',
    borderRadius: 'var(--radius-lg)',
    backgroundColor: 'var(--bg-surface)',
    border: '1px solid var(--border)',
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
  },
  cardSectionTitle: {
    fontSize: '1.1rem',
    fontWeight: '600',
    color: 'var(--accent-blue)',
    fontFamily: 'var(--font-display)',
  },
  strategyBody: {
    fontSize: '0.95rem',
    color: 'var(--text-primary)',
    lineHeight: '1.6',
    whiteSpace: 'pre-wrap',
  },
  letterPreview: {
    whiteSpace: 'pre-wrap',
    fontFamily: 'var(--font-mono)',
    fontSize: '0.9rem',
    color: 'var(--text-primary)',
    lineHeight: '1.5',
    backgroundColor: 'var(--bg-card)',
    padding: '1.25rem',
    borderRadius: 'var(--radius)',
    border: '1px solid var(--border)',
  },
  emptyState: {
    textAlign: 'center',
    padding: '3rem',
    color: 'var(--text-secondary)',
    backgroundColor: 'var(--bg-surface)',
    borderRadius: 'var(--radius-lg)',
    border: '1px solid var(--border)',
  },
  errorAlert: {
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid rgba(239, 68, 68, 0.2)',
    color: 'var(--accent-red)',
    padding: '1rem',
    borderRadius: 'var(--radius)',
    fontSize: '0.95rem',
  }
};
