import React, { useState, useEffect } from 'react';
import api from '../api';

export default function NegotiationEmail({ token, preselectedLoanId }) {
  const [loans, setLoans] = useState([]);
  const [selectedLoanId, setSelectedLoanId] = useState('');
  const [letterText, setLetterText] = useState('');
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      // Get all active loans for the dropdown selection
      const response = await api.get('/loans');
      setLoans(response.data);

      if (response.data.length > 0) {
        const defaultId = preselectedLoanId || response.data[0].loan_id;
        setSelectedLoanId(defaultId);
        // Pre-fetch/generate letter for the default selected loan
        handleGenerate(defaultId, response.data);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load loan data');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async (loanId, loanList = loans) => {
    if (!loanId) return;
    setGenerating(true);
    setError('');
    try {
      // Call the endpoint to generate the email
      const response = await api.get(`/generate-negotiation-email/${loanId}`);
      setLetterText(response.data.body);
    } catch (err) {
      // Fallback fallback template if generating fails
      const loan = loanList.find(l => l.loan_id === parseInt(loanId));
      if (loan) {
        setLetterText(`Subject: Request for One-Time Settlement - Loan Account

To,
The Retirement Department,
${loan.lender_name}

Dear Sir / Madam,

I am writing to formally request a One-Time Settlement (OTS) for my outstanding loan account.

ACCOUNT DETAILS:
Lender            : ${loan.lender_name}
Outstanding Amount: Rs. ${loan.outstanding_amount.toLocaleString()}
Monthly EMI       : Rs. ${loan.emi ? loan.emi.toLocaleString() : 'N/A'}
Overdue Period    : ${loan.overdue_months} months

FINANCIAL SITUATION:
Due to genuine financial hardship, I am unable to continue servicing my loan as per the original schedule. My monthly income is Rs. 0.00 against total expenses of Rs. 0.00, leaving minimal surplus after essential needs.

SETTLEMENT PROPOSAL:
I respectfully propose a One-Time Settlement of 60.0% of the outstanding amount.
Settlement Amount: Rs. ${(loan.outstanding_amount * 0.6).toLocaleString()}

I can arrange this payment within 30-45 days of receiving written settlement confirmation.

MY REQUESTS:
1. Written settlement offer with clear terms
2. Waiver of penal interest and charges
3. No-Objection Certificate (NOC) upon payment
4. Account closure with "Settled" status on credit report

I assure you of my genuine intention to resolve this matter promptly.

Yours sincerely,
[Your Full Name]
[Loan Account Number]
[Contact Number]
[Date]`);
      }
    } finally {
      setGenerating(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [token, preselectedLoanId]);

  const handleCopy = () => {
    if (!letterText) return;
    navigator.clipboard.writeText(letterText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) {
    return <div style={styles.loadingContainer}>Loading negotiation tools...</div>;
  }

  return (
    <div style={styles.container}>
      <div>
        <h1 style={styles.title}>✉️ Negotiation Email Generator</h1>
        <p style={styles.subtitle}>AI-tailored proposals and letters to send to your lenders.</p>
      </div>

      {error && <div style={styles.errorAlert}>{error}</div>}

      {loans.length === 0 ? (
        <div style={styles.emptyState}>
          <p>No active loans found. Please add a loan in the Dashboard before generating letters.</p>
        </div>
      ) : (
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Generate a Negotiation Letter</h3>
          <p style={styles.cardSubtitle}>Select a loan and we will write a professional settlement request.</p>
          
          <div style={styles.formRow}>
            <div style={styles.selectWrapper}>
              <label style={styles.label}>Select Loan</label>
              <select 
                value={selectedLoanId} 
                onChange={(e) => setSelectedLoanId(e.target.value)} 
                style={styles.select}
              >
                {loans.map(l => (
                  <option key={l.loan_id} value={l.loan_id}>
                    {l.lender_name} — ₹{l.outstanding_amount.toLocaleString()}
                  </option>
                ))}
              </select>
            </div>
            <button 
              onClick={() => handleGenerate(selectedLoanId)} 
              disabled={generating}
              style={styles.priBtn}
            >
              ✉️ {generating ? 'Generating...' : 'Generate Letter'}
            </button>
          </div>
        </div>
      )}

      {/* Generated letter card */}
      {letterText && (
        <div style={styles.letterCard}>
          <div style={styles.letterHeader}>
            <h3 style={styles.letterTitle}>📄 Generated Letter</h3>
            <button onClick={handleCopy} style={styles.copyBtn}>
              {copied ? '✅ Copied' : '📋 Copy'}
            </button>
          </div>
          <div style={styles.letterBody}>
            <pre style={styles.letterText}>{letterText}</pre>
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
    gap: '2.5rem',
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
  card: {
    padding: '1.75rem',
    borderRadius: 'var(--radius-lg)',
    backgroundColor: 'var(--bg-card)',
    border: '1px solid var(--border)',
    transition: 'border-color var(--transition-fast)',
  },
  cardTitle: {
    fontSize: '1.25rem',
    fontWeight: '700',
    marginBottom: '0.25rem',
    fontFamily: 'var(--font-display)',
    color: 'var(--text-primary)',
  },
  cardSubtitle: {
    fontSize: '0.85rem',
    color: 'var(--text-secondary)',
    marginBottom: '1.5rem',
  },
  formRow: {
    display: 'flex',
    alignItems: 'flex-end',
    gap: '1.5rem',
  },
  selectWrapper: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
  },
  label: {
    fontSize: '0.85rem',
    color: 'var(--text-secondary)',
  },
  select: {
    padding: '0.75rem 1rem',
    borderRadius: 'var(--radius)',
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    border: '1px solid var(--border)',
    color: 'var(--text-primary)',
    fontSize: '0.95rem',
    outline: 'none',
    fontFamily: 'var(--font-body)',
  },
  priBtn: {
    padding: '0.75rem 1.5rem',
    backgroundColor: 'var(--accent-blue)',
    color: '#ffffff',
    border: 'none',
    borderRadius: 'var(--radius)',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all var(--transition-fast)',
    height: '2.75rem',
    fontFamily: 'var(--font-body)',
  },
  letterCard: {
    borderRadius: 'var(--radius-lg)',
    border: '1px solid var(--border)',
    backgroundColor: 'var(--bg-card)',
    overflow: 'hidden',
  },
  letterHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '1.25rem 2rem',
    borderBottom: '1px solid var(--border)',
  },
  letterTitle: {
    fontSize: '1.1rem',
    fontWeight: '600',
    fontFamily: 'var(--font-display)',
    color: 'var(--text-primary)',
  },
  copyBtn: {
    padding: '0.5rem 1rem',
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    color: 'var(--text-primary)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    fontSize: '0.85rem',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all var(--transition-fast)',
    fontFamily: 'var(--font-body)',
  },
  letterBody: {
    padding: '2.5rem',
    backgroundColor: 'var(--bg-surface)',
  },
  letterText: {
    whiteSpace: 'pre-wrap',
    fontFamily: 'var(--font-mono)',
    fontSize: '0.95rem',
    color: 'var(--text-primary)',
    lineHeight: '1.6',
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
