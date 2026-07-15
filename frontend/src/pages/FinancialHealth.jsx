import React, { useState, useEffect } from 'react';
import api from '../api';

export default function FinancialHealth({ token }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchFinancialData = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await api.get('/dashboard-data');
      setData(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load financial health data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFinancialData();
  }, [token]);

  if (loading) {
    return <div style={styles.loadingContainer}>Analyzing financial indicators and ratios...</div>;
  }

  if (error) {
    return (
      <div style={styles.container}>
        <h1 style={styles.title}>Financial Health</h1>
        <div style={styles.errorAlert}>{error}</div>
      </div>
    );
  }

  const { financial_profile, loans, summary } = data || {};
  
  const income = financial_profile?.monthly_income || 0;
  const expenses = financial_profile?.monthly_expenses || 0;
  const existingDebts = financial_profile?.existing_debts || 0;
  const totalEmi = summary?.total_emi || loans?.reduce((sum, ln) => sum + (ln.emi || 0), 0) || 0;
  const totalOutstanding = summary?.total_outstanding || loans?.reduce((sum, ln) => sum + ln.outstanding_amount, 0) || 0;

  // Calculations
  const surplus = income - expenses - totalEmi;
  const emiRatio = income > 0 ? ((totalEmi / income) * 100) : 0.0;
  const dtiRatio = income > 0 ? ((totalOutstanding / income) * 100) : 0.0;

  // Determine stress level & stress description text
  let stressLevel = 'LOW';
  let stressText = 'Low stress. You are managing debt well.';
  let stressColor = 'var(--accent-green)'; // Green

  if (emiRatio > 50 || dtiRatio > 150) {
    stressLevel = 'HIGH';
    stressText = 'Critical debt stress levels detected. Action on settlements recommended.';
    stressColor = 'var(--accent-red)'; // Red
  } else if (emiRatio >= 30 || dtiRatio >= 80) {
    stressLevel = 'MEDIUM';
    stressText = 'Moderate debt stress detected. Consolidating payments could reduce pressure.';
    stressColor = 'var(--accent-amber)'; // Amber
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>💚 Financial Health</h1>
          <p style={styles.subtitle}>Detailed analysis of your debt stress and repayment capacity.</p>
        </div>
      </div>

      {/* Overall Financial Stress */}
      <div style={styles.stressCard}>
        <div style={styles.stressHeader}>
          <div style={styles.stressMessage}>
            <span style={{ fontSize: '1.2rem', color: stressColor }}>■</span>
            <span style={styles.stressText}>{stressText}</span>
          </div>
          <span style={{ 
            ...styles.stressBadge, 
            color: stressColor, 
            backgroundColor: 'rgba(255,255,255,0.03)',
            borderColor: stressColor
          }}>
            {stressLevel}
          </span>
        </div>
      </div>

      {/* Financial Metrics row */}
      <div style={styles.metricsRow}>
        <div style={styles.metricCard}>
          <span style={styles.metricLabel}>MONTHLY INCOME</span>
          <span style={styles.metricVal}>₹ {income.toLocaleString('en-IN')}</span>
        </div>
        <div style={styles.metricCard}>
          <span style={styles.metricLabel}>MONTHLY EXPENSES</span>
          <span style={styles.metricVal}>₹ {expenses.toLocaleString('en-IN')}</span>
        </div>
        <div style={{ ...styles.metricCard, borderLeft: '3px solid var(--accent-green)' }}>
          <span style={styles.metricLabel}>MONTHLY SURPLUS</span>
          <span style={{ ...styles.metricVal, color: surplus >= 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
            ₹ {surplus.toLocaleString('en-IN')}
          </span>
        </div>
        <div style={styles.metricCard}>
          <span style={styles.metricLabel}>LUMP SUM PAYMENTS</span>
          <span style={styles.metricVal}>₹ {existingDebts.toLocaleString('en-IN')}</span>
        </div>
      </div>

      {/* Ratios row */}
      <div style={styles.ratiosGrid}>
        <div style={styles.ratioCard}>
          <div style={styles.ratioHeader}>
            <span style={styles.ratioTitle}>EMI-to-Income Ratio</span>
            <span style={styles.ratioVal}>{emiRatio.toFixed(1)}%</span>
          </div>
          {/* Progress bar */}
          <div style={styles.progressBg}>
            <div style={{ ...styles.progressFill, width: `${Math.min(100, emiRatio)}%`, backgroundColor: getScoreColor(100 - emiRatio * 1.3) }} />
          </div>
          <span style={styles.ratioHelp}>Ideal: below 30% - 40% - Healthy range</span>
        </div>

        <div style={styles.ratioCard}>
          <div style={styles.ratioHeader}>
            <span style={styles.ratioTitle}>Debt-to-Income Ratio</span>
            <span style={styles.ratioVal}>{dtiRatio.toFixed(1)}%</span>
          </div>
          <div style={styles.progressBg}>
            <div style={{ ...styles.progressFill, width: `${Math.min(100, dtiRatio / 2.5)}%`, backgroundColor: getScoreColor(100 - dtiRatio * 0.4) }} />
          </div>
          <span style={styles.ratioHelp}>Ideal: below 50% - 80% - Manageable range</span>
        </div>
      </div>

      {/* Improvement Tips */}
      <div style={styles.tipsCard}>
        <h2 style={styles.tipsTitle}>💡 Improvement Tips</h2>
        <p style={styles.tipsSubtitle}>Based on your financial profile</p>
        <div style={styles.tipsGrid}>
          <div style={styles.tipItem}>
            <span style={styles.tipIcon}>📉</span>
            <span style={styles.tipText}>Reduce discretionary spending to increase surplus.</span>
          </div>
          <div style={styles.tipItem}>
            <span style={styles.tipIcon}>🏛️</span>
            <span style={styles.tipText}>Contact lenders for EMI restructuring options.</span>
          </div>
          <div style={styles.tipItem}>
            <span style={styles.tipIcon}>⚠️</span>
            <span style={styles.tipText}>Use lump sum for highest-interest loan first.</span>
          </div>
          <div style={styles.tipItem}>
            <span style={styles.tipIcon}>📋</span>
            <span style={styles.tipText}>Track all expenses to find savings opportunities.</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// Color helper
const getScoreColor = (score) => {
  if (score >= 65) return 'var(--accent-green)'; // Green
  if (score >= 35) return 'var(--accent-amber)'; // Amber
  return 'var(--accent-red)'; // Red
};

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
  stressCard: {
    backgroundColor: 'var(--bg-surface)',
    borderRadius: 'var(--radius-lg)',
    border: '1px solid var(--border)',
    padding: '1.5rem',
    transition: 'border-color var(--transition-fast)',
  },
  stressHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  stressMessage: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
  },
  stressText: {
    fontSize: '0.95rem',
    color: 'var(--text-primary)',
    fontWeight: '500',
  },
  stressBadge: {
    padding: '0.35rem 0.75rem',
    borderRadius: '0.5rem',
    fontSize: '0.85rem',
    fontWeight: '700',
    border: '1px solid',
  },
  metricsRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: '1.5rem',
  },
  metricCard: {
    padding: '1.5rem',
    borderRadius: 'var(--radius-lg)',
    backgroundColor: 'var(--bg-surface)',
    border: '1px solid var(--border)',
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
    transition: 'transform var(--transition-fast)',
  },
  metricLabel: {
    fontSize: '0.8rem',
    color: 'var(--text-secondary)',
    fontWeight: '500',
  },
  metricVal: {
    fontSize: '1.5rem',
    fontWeight: '700',
    fontFamily: 'var(--font-display)',
  },
  ratiosGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '2rem',
  },
  ratioCard: {
    padding: '1.75rem',
    borderRadius: 'var(--radius-lg)',
    backgroundColor: 'var(--bg-surface)',
    border: '1px solid var(--border)',
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
    transition: 'border-color var(--transition-fast)',
  },
  ratioHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  ratioTitle: {
    fontSize: '1.1rem',
    fontWeight: '600',
    fontFamily: 'var(--font-display)',
  },
  ratioVal: {
    fontSize: '1.25rem',
    fontWeight: '700',
  },
  progressBg: {
    width: '100%',
    height: '0.5rem',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: '0.25rem',
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: '0.25rem',
    transition: 'width 0.3s ease',
  },
  ratioHelp: {
    fontSize: '0.8rem',
    color: 'var(--text-secondary)',
  },
  tipsCard: {
    padding: '1.75rem',
    borderRadius: 'var(--radius-lg)',
    backgroundColor: 'var(--bg-card)',
    border: '1px solid var(--border)',
  },
  tipsTitle: {
    fontSize: '1.25rem',
    fontWeight: '600',
    fontFamily: 'var(--font-display)',
    marginBottom: '0.25rem',
  },
  tipsSubtitle: {
    fontSize: '0.85rem',
    color: 'var(--text-secondary)',
    marginBottom: '1.5rem',
  },
  tipsGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '1.25rem',
  },
  tipItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
    padding: '1rem',
    borderRadius: 'var(--radius)',
    backgroundColor: 'rgba(255, 255, 255, 0.02)',
    border: '1px solid rgba(255, 255, 255, 0.04)',
    transition: 'background-color var(--transition-fast)',
  },
  tipIcon: {
    fontSize: '1.25rem',
  },
  tipText: {
    fontSize: '0.9rem',
    color: 'var(--text-primary)',
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
