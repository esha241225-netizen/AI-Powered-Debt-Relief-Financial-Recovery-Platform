import React, { useState, useEffect } from 'react';
import api from '../api';

export default function Dashboard({ token, user }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Profile fields
  const [income, setIncome] = useState(90000);
  const [expenses, setExpenses] = useState(40000);
  const [debts, setDebts] = useState(8000);
  const [showProfileForm, setShowProfileForm] = useState(false);

  // New loan fields
  const [showAddLoan, setShowAddLoan] = useState(false);
  const [loanType, setLoanType] = useState('Personal Loan');
  const [lenderName, setLenderName] = useState('');
  const [loanAmount, setLoanAmount] = useState('');
  const [outstanding, setOutstanding] = useState('');
  const [interest, setInterest] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [overdue, setOverdue] = useState('0');
  const [emi, setEmi] = useState('');

  const fetchDashboardData = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await api.get('/dashboard-data');
      setData(response.data);

      if (response.data.financial_profile) {
        setIncome(response.data.financial_profile.monthly_income);
        setExpenses(response.data.financial_profile.monthly_expenses);
        setDebts(response.data.financial_profile.existing_debts);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [token]);

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await api.put('/update-profile', {
        user_id: user.user_id,
        monthly_income: parseFloat(income),
        monthly_expenses: parseFloat(expenses),
        existing_debts: parseFloat(debts)
      });
      setShowProfileForm(false);
      fetchDashboardData();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to update profile');
    }
  };

  const handleAddLoan = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await api.post('/add-loan', {
        user_id: user.user_id,
        loan_type: loanType,
        lender_name: lenderName,
        loan_amount: parseFloat(loanAmount),
        outstanding_amount: parseFloat(outstanding),
        interest_rate: parseFloat(interest),
        due_date: dueDate,
        overdue_months: parseInt(overdue),
        emi: emi ? parseFloat(emi) : null
      });
      setShowAddLoan(false);
      setLenderName('');
      setLoanAmount('');
      setOutstanding('');
      setInterest('');
      setDueDate('');
      setOverdue('0');
      setEmi('');
      fetchDashboardData();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to add loan');
    }
  };

  const handleDeleteLoan = async (loanId) => {
    if (!window.confirm('Are you sure you want to delete this loan?')) return;
    try {
      await api.delete(`/delete-loan/${loanId}`);
      fetchDashboardData();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to delete loan');
    }
  };

  if (loading) {
    return <div style={styles.loadingContainer}>Loading dashboard overview...</div>;
  }

  const { financial_profile, loans, summary, loan_priorities } = data || {};
  
  // Calculations matching backend models
  const totalOutstanding = summary?.total_outstanding || 0;
  const totalLoans = summary?.total_loans || 0;
  const totalEmi = loans?.reduce((sum, l) => sum + (l.emi || 0), 0) || 0;
  const surplus = income - expenses - totalEmi;
  const dtiRatio = income > 0 ? ((totalOutstanding / income) * 100) : 0.0;
  const emiRatio = income > 0 ? ((totalEmi / income) * 100) : 0.0;

  // Determine stress level & stress color
  const stressLevel = emiRatio > 50 ? 'HIGH' : (emiRatio >= 30 ? 'MEDIUM' : 'LOW');
  const stressColor = stressLevel === 'HIGH' ? 'var(--accent-red)' : (stressLevel === 'MEDIUM' ? 'var(--accent-amber)' : 'var(--accent-green)');

  return (
    <div style={styles.container}>
      {/* Title block */}
      <div>
        <h1 style={styles.title}>Dashboard Overview</h1>
        <p style={styles.subtitle}>Your financial snapshot at a glance</p>
      </div>

      {error && <div style={styles.errorAlert}>{error}</div>}

      {/* Row of 5 status cards */}
      <div style={styles.statsRow}>
        <div style={styles.statCard}>
          <span style={styles.statLabel}>MONTHLY SURPLUS</span>
          <span style={{ ...styles.statVal, color: surplus >= 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
            ₹ {surplus.toLocaleString('en-IN')}
          </span>
          <span style={styles.statSub}>After all expenses</span>
        </div>
        <div style={styles.statCard}>
          <span style={styles.statLabel}>TOTAL OUTSTANDING</span>
          <span style={styles.statVal}>₹ {totalOutstanding.toLocaleString('en-IN')}</span>
          <span style={styles.statSub}>{totalLoans} active loans</span>
        </div>
        <div style={styles.statCard}>
          <span style={styles.statLabel}>TOTAL EMI</span>
          <span style={styles.statVal}>₹ {totalEmi.toLocaleString('en-IN')}</span>
          <span style={styles.statSub}>{emiRatio.toFixed(1)}% of Income</span>
        </div>
        <div style={styles.statCard}>
          <span style={styles.statLabel}>DEBT-TO-INCOME</span>
          <span style={styles.statVal}>{dtiRatio.toFixed(1)}%</span>
          <span style={styles.statSub}>Ratio</span>
        </div>
        <div style={styles.statCard}>
          <span style={styles.statLabel}>STRESS LEVEL</span>
          <div style={styles.badgeWrapper}>
            <span style={{ 
              ...styles.stressBadge, 
              color: stressColor, 
              backgroundColor: 'rgba(255,255,255,0.03)',
              borderColor: stressColor
            }}>
              {stressLevel}
            </span>
          </div>
          <span style={styles.statSub}>Financial stress index</span>
        </div>
      </div>

      {/* Financial Profile details */}
      <div style={styles.card}>
        <div style={styles.cardHeader}>
          <div>
            <h3 style={styles.cardTitle}>Financial Profile</h3>
            <p style={styles.cardSubtitle}>Your income and expense baseline</p>
          </div>
          <button onClick={() => setShowProfileForm(true)} style={styles.editBtn}>
            ✏️ Edit Profile
          </button>
        </div>

        <div style={styles.profileDetails}>
          <div style={styles.profileItem}>
            <span style={styles.profileLabel}>Monthly Income</span>
            <span style={styles.profileVal}>₹ {income.toLocaleString('en-IN')}</span>
          </div>
          <div style={styles.profileItem}>
            <span style={styles.profileLabel}>Monthly Expenses</span>
            <span style={styles.profileVal}>₹ {expenses.toLocaleString('en-IN')}</span>
          </div>
          <div style={styles.profileItem}>
            <span style={styles.profileLabel}>Lump Sum Available</span>
            <span style={styles.profileVal}>₹ {debts.toLocaleString('en-IN')}</span>
          </div>
        </div>
      </div>

      {/* Active loans table */}
      <div style={styles.card}>
        <div style={styles.cardHeader}>
          <div>
            <h3 style={styles.cardTitle}>Active Loans</h3>
            <p style={styles.cardSubtitle}>Manage your debt portfolio</p>
          </div>
          <button onClick={() => setShowAddLoan(true)} style={styles.priBtn}>
            + Add Loan
          </button>
        </div>

        {(!loans || loans.length === 0) ? (
          <div style={styles.emptyState}>
            <p>No active loans registered.</p>
          </div>
        ) : (
          <div style={styles.tableWrapper}>
            <table style={styles.table}>
              <thead>
                <tr style={styles.thRow}>
                  <th style={styles.th}>LENDER</th>
                  <th style={styles.th}>TYPE</th>
                  <th style={styles.th}>OUTSTANDING</th>
                  <th style={styles.th}>INTEREST</th>
                  <th style={styles.th}>EMI</th>
                  <th style={styles.th}>OVERDUE</th>
                  <th style={styles.th}>PRIORITY</th>
                  <th style={styles.th}>ACTION</th>
                </tr>
              </thead>
              <tbody>
                {loans.map((loan) => {
                  const pItem = loan_priorities?.find(p => p.loan_id === loan.loan_id);
                  const priority = pItem?.priority || 'Low';
                  const priorityColor = priority === 'High' ? 'var(--accent-red)' : (priority === 'Medium' ? 'var(--accent-amber)' : 'var(--accent-green)');

                  return (
                    <tr key={loan.loan_id} style={styles.tr}>
                      <td style={styles.tdBold}>{loan.lender_name}</td>
                      <td style={styles.td}>
                        <span style={styles.typeBadge}>{loan.loan_type}</span>
                      </td>
                      <td style={styles.tdBold}>₹ {loan.outstanding_amount.toLocaleString('en-IN')}</td>
                      <td style={styles.td}>{loan.interest_rate}%</td>
                      <td style={styles.td}>₹ {(loan.emi || 0).toLocaleString('en-IN')}</td>
                      <td style={{ ...styles.td, color: loan.overdue_months > 0 ? 'var(--accent-red)' : 'var(--text-secondary)' }}>
                        {loan.overdue_months} mo.
                      </td>
                      <td style={styles.td}>
                        <span style={{ 
                          ...styles.priorityBadge, 
                          color: priorityColor, 
                          backgroundColor: 'rgba(255,255,255,0.03)',
                          borderColor: priorityColor
                        }}>
                          {priority.toUpperCase()}
                        </span>
                      </td>
                      <td style={styles.td}>
                        <button onClick={() => handleDeleteLoan(loan.loan_id)} style={styles.deleteBtn}>
                          Delete
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Edit Profile Modal */}
      {showProfileForm && (
        <div style={styles.modalOverlay}>
          <div style={styles.modal}>
            <h3 style={styles.modalTitle}>Update Financial Profile</h3>
            <form onSubmit={handleUpdateProfile} style={styles.modalForm}>
              <div style={styles.formGroup}>
                <label style={styles.label}>Monthly Income (INR)</label>
                <input type="number" value={income} onChange={(e) => setIncome(e.target.value)} required style={styles.input} />
              </div>
              <div style={styles.formGroup}>
                <label style={styles.label}>Monthly Expenses (INR)</label>
                <input type="number" value={expenses} onChange={(e) => setExpenses(e.target.value)} required style={styles.input} />
              </div>
              <div style={styles.formGroup}>
                <label style={styles.label}>Lump Sum Available (INR)</label>
                <input type="number" value={debts} onChange={(e) => setDebts(e.target.value)} required style={styles.input} />
              </div>
              <div style={styles.modalActions}>
                <button type="button" onClick={() => setShowProfileForm(false)} style={styles.modalCancel}>Cancel</button>
                <button type="submit" style={styles.modalSubmit}>Save Changes</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Loan Modal */}
      {showAddLoan && (
        <div style={styles.modalOverlay}>
          <div style={styles.modal}>
            <h3 style={styles.modalTitle}>Add Loan Record</h3>
            <form onSubmit={handleAddLoan} style={styles.modalForm}>
              <div style={styles.formGroup}>
                <label style={styles.label}>Loan Type</label>
                <select value={loanType} onChange={(e) => setLoanType(e.target.value)} style={styles.input}>
                  <option value="Personal Loan">Personal Loan</option>
                  <option value="Credit Card">Credit Card</option>
                  <option value="Home Loan">Home Loan</option>
                  <option value="Auto Loan">Auto Loan</option>
                  <option value="Education Loan">Education Loan</option>
                  <option value="Business Loan">Business Loan</option>
                </select>
              </div>
              <div style={styles.formGroup}>
                <label style={styles.label}>Lender Name</label>
                <input type="text" value={lenderName} onChange={(e) => setLenderName(e.target.value)} placeholder="e.g. KISHT" required style={styles.input} />
              </div>
              <div style={styles.modalRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Sanctioned Amount (INR)</label>
                  <input type="number" value={loanAmount} onChange={(e) => setLoanAmount(e.target.value)} required style={styles.input} />
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Outstanding Balance (INR)</label>
                  <input type="number" value={outstanding} onChange={(e) => setOutstanding(e.target.value)} required style={styles.input} />
                </div>
              </div>
              <div style={styles.modalRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Interest Rate (% p.a.)</label>
                  <input type="number" step="0.01" value={interest} onChange={(e) => setInterest(e.target.value)} required style={styles.input} />
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Overdue Months</label>
                  <input type="number" value={overdue} onChange={(e) => setOverdue(e.target.value)} required style={styles.input} />
                </div>
              </div>
              <div style={styles.modalRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>EMI (INR, optional)</label>
                  <input type="number" value={emi} onChange={(e) => setEmi(e.target.value)} style={styles.input} />
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Due Date</label>
                  <input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} required style={styles.input} />
                </div>
              </div>
              <div style={styles.modalActions}>
                <button type="button" onClick={() => setShowAddLoan(false)} style={styles.modalCancel}>Cancel</button>
                <button type="submit" style={styles.modalSubmit}>Add Loan</button>
              </div>
            </form>
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
  statsRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(5, 1fr)',
    gap: '1.25rem',
  },
  statCard: {
    padding: '1.25rem',
    borderRadius: 'var(--radius-lg)',
    backgroundColor: 'var(--bg-surface)',
    border: '1px solid var(--border)',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
    minHeight: '7.5rem',
    transition: 'transform var(--transition-fast)',
  },
  statLabel: {
    fontSize: '0.75rem',
    color: 'var(--text-secondary)',
    fontWeight: '500',
  },
  statVal: {
    fontSize: '1.35rem',
    fontWeight: '700',
    fontFamily: 'var(--font-display)',
    margin: '0.5rem 0',
  },
  statSub: {
    fontSize: '0.75rem',
    color: 'var(--text-secondary)',
  },
  badgeWrapper: {
    margin: '0.5rem 0',
  },
  stressBadge: {
    padding: '0.25rem 0.5rem',
    borderRadius: '0.375rem',
    fontSize: '0.75rem',
    fontWeight: '700',
    border: '1px solid',
    display: 'inline-block',
  },
  card: {
    padding: '1.75rem',
    borderRadius: 'var(--radius-lg)',
    backgroundColor: 'var(--bg-card)',
    border: '1px solid var(--border)',
    display: 'flex',
    flexDirection: 'column',
    gap: '1.5rem',
    transition: 'border-color var(--transition-fast)',
  },
  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardTitle: {
    fontSize: '1.2rem',
    fontWeight: '600',
    color: 'var(--text-primary)',
    fontFamily: 'var(--font-display)',
  },
  cardSubtitle: {
    fontSize: '0.85rem',
    color: 'var(--text-secondary)',
  },
  editBtn: {
    padding: '0.5rem 1rem',
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    color: 'var(--text-primary)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    fontSize: '0.85rem',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all var(--transition-fast)',
  },
  priBtn: {
    padding: '0.5rem 1rem',
    backgroundColor: 'var(--accent-blue)',
    color: '#ffffff',
    border: 'none',
    borderRadius: 'var(--radius)',
    fontSize: '0.85rem',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all var(--transition-fast)',
  },
  profileDetails: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '2rem',
  },
  profileItem: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
  },
  profileLabel: {
    fontSize: '0.85rem',
    color: 'var(--text-secondary)',
  },
  profileVal: {
    fontSize: '1.25rem',
    fontWeight: '700',
    color: 'var(--text-primary)',
  },
  tableWrapper: {
    overflowX: 'auto',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    textAlign: 'left',
  },
  thRow: {
    borderBottom: '1px solid var(--border)',
  },
  th: {
    padding: '1rem',
    fontSize: '0.8rem',
    fontWeight: '600',
    color: 'var(--text-secondary)',
  },
  tr: {
    borderBottom: '1px solid var(--border)',
    transition: 'background-color var(--transition-fast)',
  },
  td: {
    padding: '1rem',
    fontSize: '0.85rem',
    color: 'var(--text-primary)',
  },
  tdBold: {
    padding: '1rem',
    fontSize: '0.85rem',
    color: 'var(--text-primary)',
    fontWeight: '600',
  },
  typeBadge: {
    padding: '0.2rem 0.5rem',
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    fontSize: '0.75rem',
    color: 'var(--text-secondary)',
  },
  priorityBadge: {
    padding: '0.2rem 0.5rem',
    borderRadius: '0.375rem',
    fontSize: '0.75rem',
    fontWeight: '700',
    border: '1px solid',
  },
  deleteBtn: {
    padding: '0.35rem 0.75rem',
    backgroundColor: 'rgba(239, 68, 68, 0.05)',
    color: 'var(--accent-red)',
    border: '1px solid rgba(239, 68, 68, 0.1)',
    borderRadius: 'var(--radius)',
    fontSize: '0.8rem',
    cursor: 'pointer',
    transition: 'all var(--transition-fast)',
  },
  emptyState: {
    padding: '2rem',
    color: 'var(--text-secondary)',
    textAlign: 'center',
  },
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(6, 9, 18, 0.85)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 100,
    backdropFilter: 'blur(4px)',
    animation: 'fadeIn var(--transition-normal)',
  },
  modal: {
    width: '100%',
    maxWidth: '30rem',
    backgroundColor: 'var(--bg-card)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-lg)',
    padding: '2rem',
    animation: 'modalFadeIn var(--transition-normal)',
  },
  modalTitle: {
    fontSize: '1.5rem',
    fontWeight: '700',
    marginBottom: '1.5rem',
    fontFamily: 'var(--font-display)',
  },
  modalForm: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1.25rem',
  },
  modalRow: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '1.25rem',
  },
  formGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
  },
  label: {
    fontSize: '0.85rem',
    color: 'var(--text-secondary)',
  },
  input: {
    padding: '0.75rem 1rem',
    borderRadius: 'var(--radius)',
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    border: '1px solid var(--border)',
    color: 'var(--text-primary)',
    fontSize: '0.95rem',
    outline: 'none',
    fontFamily: 'var(--font-body)',
  },
  modalActions: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '1rem',
    marginTop: '1rem',
  },
  modalCancel: {
    padding: '0.75rem 1.25rem',
    backgroundColor: 'transparent',
    color: 'var(--text-secondary)',
    border: 'none',
    borderRadius: 'var(--radius)',
    fontWeight: '600',
    cursor: 'pointer',
    fontFamily: 'var(--font-body)',
  },
  modalSubmit: {
    padding: '0.75rem 1.5rem',
    backgroundColor: 'var(--accent-blue)',
    color: '#ffffff',
    border: 'none',
    borderRadius: 'var(--radius)',
    fontWeight: '600',
    cursor: 'pointer',
    fontFamily: 'var(--font-body)',
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
