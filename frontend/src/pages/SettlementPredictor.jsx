import React, { useState, useEffect } from 'react';
import api from '../api';

export default function SettlementPredictor({ token, onSelectLetter }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Strategy state
  const [strategy, setStrategy] = useState(null);
  const [loadingStrategy, setLoadingStrategy] = useState(false);
  const [selectedLoanId, setSelectedLoanId] = useState(null);

  const fetchPredictions = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await api.get('/settlement-predictor');
      setData(response.data);
      
      // Auto-select first loan strategy if available
      if (response.data.settlement_results?.length > 0) {
        const firstLoan = response.data.settlement_results[0];
        setSelectedLoanId(firstLoan.loan_id);
        fetchStrategy(firstLoan.loan_id);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to compute settlement predictions. Verify you have registered loans.');
    } finally {
      setLoading(false);
    }
  };

  const fetchStrategy = async (loanId) => {
    setLoadingStrategy(true);
    try {
      const response = await api.get(`/ai-negotiation-strategy?loan_id=${loanId}`);
      setStrategy(response.data.negotiation_strategy);
    } catch (err) {
      // Fallback strategy template if AI or DB fails
      const loan = data?.settlement_results?.find(l => l.loan_id === loanId);
      if (loan) {
        setStrategy(`
=========================================
💼 FINANCIAL NEGOTIATION STRATEGY
=========================================

🔒 YOUR FINANCIAL SNAPSHOT:
• Monthly Surplus: INR ${data.surplus?.toLocaleString()}
• Debt ratio: ${data.emi_ratio_percent}% of income
• Stress Level: ${data.settlement_results[0]?.priority}

📌 NEGOTIATION PLAN:
• Lender: ${loan.lender_name}
• Outstanding: INR ${loan.outstanding_amount.toLocaleString()}
• Settlement Offer: INR ${loan.recommended_settlement_amount.toLocaleString()} (60.0% of outstanding)
• Risk Level: ${loan.priority}
• Approach: Negotiate EMI reduction first

🔑 KEY TALKING POINTS:
1. Emphasize genuine financial hardship with documentation
2. Request interest waiver or reduction as part of settlement
3. Get ALL settlement terms in writing before paying
4. Ask for NOC (No-Objection Certificate) post-settlement
5. Negotiate 'Full & Final Settlement' status for credit report

⚠️ DOCUMENTS TO REQUEST:
• Original loan agreement
• Complete account statement
• Written settlement offer letter
• NOC template

⏰ TIMELINE: 30-90 days for full negotiation and settlement
        `);
      }
    } finally {
      setLoadingStrategy(false);
    }
  };

  useEffect(() => {
    fetchPredictions();
  }, [token]);

  const handleLoanSelect = (loanId) => {
    setSelectedLoanId(loanId);
    fetchStrategy(loanId);
  };

  if (loading) {
    return <div style={styles.loadingContainer}>Analyzing liabilities and generating settlement models...</div>;
  }

  if (error) {
    return (
      <div style={styles.container}>
        <h1 style={styles.title}>Settlement Predictor</h1>
        <div style={styles.errorAlert}>{error}</div>
      </div>
    );
  }

  const { settlement_results } = data || {};

  return (
    <div style={styles.container}>
      <div>
        <h1 style={styles.title}>🔮 Settlement Predictor</h1>
        <p style={styles.subtitle}>AI-powered settlement estimates for each of your loans.</p>
      </div>

      {/* Row of prediction cards */}
      <div style={styles.resultsGrid}>
        {settlement_results?.map((item) => {
          const priorityColor = item.priority === 'High' ? 'var(--accent-red)' : item.priority === 'Medium' ? 'var(--accent-amber)' : 'var(--accent-green)';
          const savings = item.outstanding_amount - item.recommended_settlement_amount;
          const isSelected = selectedLoanId === item.loan_id;

          return (
            <div 
              key={item.loan_id} 
              onClick={() => handleLoanSelect(item.loan_id)}
              style={{
                ...styles.resultCard,
                ...(isSelected ? styles.resultCardActive : {})
              }}
            >
              <div style={styles.cardHeader}>
                <span style={styles.lenderName}>{item.lender_name}</span>
                <span style={{ 
                  ...styles.priorityBadge, 
                  color: priorityColor, 
                  backgroundColor: 'rgba(255,255,255,0.03)',
                  borderColor: priorityColor
                }}>
                  {item.priority.toUpperCase()} RISK
                </span>
              </div>

              <div style={styles.percentageVal}>
                {item.settlement_percentage}%
              </div>
              <div style={styles.percentageLabel}>Suggested Settlement</div>

              <div style={styles.recommendedAmt}>
                ₹ {item.recommended_settlement_amount.toLocaleString()}
              </div>
              <div style={styles.recommendedLabel}>Recommended Amount</div>

              <div style={styles.savingAlert}>
                💰 Potential saving ₹ {savings.toLocaleString()}
              </div>
            </div>
          );
        })}
      </div>

      {/* AI Negotiation Strategy Panel */}
      {selectedLoanId && (
        <div style={styles.strategySection}>
          <div style={styles.strategyHeader}>
            <div>
              <h3 style={styles.strategyTitle}>🤖 AI Negotiation Strategy</h3>
              <p style={styles.strategySubtitle}>Personalised advice based on your financial profile</p>
            </div>
            <button 
              disabled={loadingStrategy} 
              onClick={() => fetchStrategy(selectedLoanId)} 
              style={styles.priBtn}
            >
              {loadingStrategy ? 'Generating...' : 'Regenerate'}
            </button>
          </div>

          <div style={styles.strategyCard}>
            {loadingStrategy ? (
              <div style={styles.strategyLoading}>Analyzing financial profile and drafting talking points...</div>
            ) : (
              <pre style={styles.strategyText}>
                {strategy}
              </pre>
            )}
          </div>
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
  resultsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(18rem, 1fr))',
    gap: '1.5rem',
  },
  resultCard: {
    padding: '1.5rem',
    borderRadius: 'var(--radius-lg)',
    backgroundColor: 'var(--bg-surface)',
    border: '1px solid var(--border)',
    display: 'flex',
    flexDirection: 'column',
    cursor: 'pointer',
    transition: 'all var(--transition-fast)',
  },
  resultCardActive: {
    borderColor: 'var(--accent-blue)',
    boxShadow: '0 4px 20px rgba(37, 99, 235, 0.15)',
  },
  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1.5rem',
  },
  lenderName: {
    fontSize: '1.15rem',
    fontWeight: '700',
    fontFamily: 'var(--font-display)',
    color: 'var(--text-primary)',
  },
  priorityBadge: {
    padding: '0.25rem 0.5rem',
    borderRadius: '0.375rem',
    fontSize: '0.7rem',
    fontWeight: '700',
    border: '1px solid',
  },
  percentageVal: {
    fontSize: '2rem',
    fontWeight: '800',
    color: 'var(--accent-green)',
    fontFamily: 'var(--font-display)',
  },
  percentageLabel: {
    fontSize: '0.8rem',
    color: 'var(--text-secondary)',
    marginBottom: '1rem',
  },
  recommendedAmt: {
    fontSize: '1.3rem',
    fontWeight: '700',
    color: 'var(--text-primary)',
  },
  recommendedLabel: {
    fontSize: '0.8rem',
    color: 'var(--text-secondary)',
    marginBottom: '1.5rem',
  },
  savingAlert: {
    padding: '0.5rem 0.75rem',
    backgroundColor: 'rgba(59, 130, 246, 0.08)',
    borderRadius: 'var(--radius)',
    fontSize: '0.85rem',
    color: 'var(--accent-blue)',
    fontWeight: '600',
    textAlign: 'center',
  },
  strategySection: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
    marginTop: '1rem',
  },
  strategyHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  strategyTitle: {
    fontSize: '1.25rem',
    fontWeight: '700',
    fontFamily: 'var(--font-display)',
    color: 'var(--text-primary)',
  },
  strategySubtitle: {
    fontSize: '0.85rem',
    color: 'var(--text-secondary)',
  },
  priBtn: {
    padding: '0.65rem 1.25rem',
    backgroundColor: 'var(--accent-blue)',
    color: '#ffffff',
    border: 'none',
    borderRadius: 'var(--radius)',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all var(--transition-fast)',
    fontFamily: 'var(--font-body)',
  },
  strategyCard: {
    backgroundColor: 'var(--bg-card)',
    borderRadius: 'var(--radius-lg)',
    border: '1px solid var(--border)',
    padding: '2rem',
  },
  strategyLoading: {
    color: 'var(--text-secondary)',
    fontSize: '0.95rem',
  },
  strategyText: {
    whiteSpace: 'pre-wrap',
    fontFamily: 'var(--font-mono)',
    fontSize: '0.9rem',
    color: 'var(--text-primary)',
    lineHeight: '1.6',
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
