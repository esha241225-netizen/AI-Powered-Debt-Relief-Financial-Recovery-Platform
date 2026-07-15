import React from 'react';

export default function KnowYourRights() {
  const rightsList = [
    {
      id: 1,
      title: "No Harassment",
      icon: "🚫",
      description: "Recovery agents CANNOT call you before 7 AM or after 7 PM. Threats, abuse, or use of force is illegal under RBI guidelines."
    },
    {
      id: 2,
      title: "Right to Statement",
      icon: "📋",
      description: "You have the right to receive a full and detailed loan account statement at any time, free of charge."
    },
    {
      id: 3,
      title: "Settlement Negotiation",
      icon: "🤝",
      description: "You can negotiate a one-time settlement with your lender. Lenders are allowed to accept partial payments to close an NPA account."
    },
    {
      id: 4,
      title: "Advance Notice Required",
      icon: "🔔",
      description: "Lenders must give you 60-day advance notice before classifying your account as NPA (Non-Performing Asset)."
    },
    {
      id: 5,
      title: "Grievance Redressal",
      icon: "🏛️",
      description: "Every bank must have a Grievance Redressal Officer. You can escalate to RBI Banking Ombudsman if unresolved in 30 days."
    },
    {
      id: 6,
      title: "NOC After Settlement",
      icon: "📄",
      description: "After full payment or settlement, you are legally entitled to a No-Objection Certificate (NOC) from the lender."
    },
    {
      id: 7,
      title: "Property Protection",
      icon: "🏢",
      description: "Lenders cannot seize property without following SARFAESI Act procedures. You have the right to challenge auction notices."
    },
    {
      id: 8,
      title: "Privacy Rights",
      icon: "🔒",
      description: "Recovery agents cannot contact your family, employers, or neighbors to pressure you for repayment."
    }
  ];

  const stepsList = [
    {
      id: "01",
      title: "Document Everything",
      description: "Keep records of all calls, letters, and communications from lenders and recovery agents."
    },
    {
      id: "02",
      title: "Request Written Settlement",
      description: "Ask for any settlement offer in writing before making any payment."
    },
    {
      id: "03",
      title: "File a Complaint",
      description: "If harassed, file a complaint with RBI Ombudsman at cms.rbi.org.in or call 14448."
    },
    {
      id: "04",
      title: "Get Legal Help",
      description: "Consult a debt settlement lawyer for large amounts. Many offer free initial consultations."
    }
  ];

  return (
    <div style={styles.container}>
      <div>
        <h1 style={styles.title}>⚖️ Know Your Rights</h1>
        <p style={styles.subtitle}>RBI guidelines and legal protections for Indian borrowers.</p>
      </div>

      {/* Header card: You Have Rights as a Borrower */}
      <div style={styles.heroCard}>
        <h3 style={styles.heroTitle}>You Have Rights as a Borrower 💪</h3>
        <p style={styles.heroText}>
          Under RBI's Fair Practices Code and the SARFAESI Act, lenders and recovery agents must follow strict rules. Knowing these rights protects you from illegal harassment and helps you negotiate from a position of strength.
        </p>
      </div>

      {/* Row of 8 rights cards */}
      <div style={styles.grid}>
        {rightsList.map((right) => (
          <div key={right.id} style={styles.card}>
            <div style={styles.cardHeader}>
              <span style={styles.icon}>{right.icon}</span>
              <h4 style={styles.cardTitle}>{right.title}</h4>
            </div>
            <p style={styles.cardBody}>{right.description}</p>
          </div>
        ))}
      </div>

      {/* What To Do If Harassed */}
      <div style={styles.stepsSection}>
        <h3 style={styles.sectionTitle}>🛡️ What To Do If Harassed</h3>
        <p style={styles.sectionSubtitle}>Step-by-step protection guide</p>
        
        <div style={styles.stepsGrid}>
          {stepsList.map((step) => (
            <div key={step.id} style={styles.stepCard}>
              <span style={styles.stepId}>{step.id}</span>
              <h4 style={styles.stepTitle}>{step.title}</h4>
              <p style={styles.stepBody}>{step.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* RBI Ombudsman Helpline Banner */}
      <div style={styles.helplineCard}>
        <div style={styles.helpLeft}>
          <h4 style={styles.helpTitle}>📞 RBI Banking Ombudsman</h4>
          <p style={styles.helpText}>Toll-free: 14448  |  Website: cms.rbi.org.in</p>
        </div>
        <a href="https://cms.rbi.org.in" target="_blank" rel="noreferrer" style={styles.priBtn}>
          File Complaint →
        </a>
      </div>
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
  heroCard: {
    padding: '1.5rem',
    borderRadius: 'var(--radius-lg)',
    backgroundColor: 'var(--bg-surface)',
    border: '1px solid var(--border)',
  },
  heroTitle: {
    fontSize: '1.25rem',
    fontWeight: '700',
    marginBottom: '0.75rem',
    fontFamily: 'var(--font-display)',
    color: 'var(--text-primary)',
  },
  heroText: {
    fontSize: '0.95rem',
    color: 'var(--text-secondary)',
    lineHeight: '1.6',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: '1.25rem',
  },
  card: {
    padding: '1.25rem',
    borderRadius: 'var(--radius-lg)',
    backgroundColor: 'var(--bg-card)',
    border: '1px solid var(--border)',
    display: 'flex',
    flexDirection: 'column',
    gap: '0.75rem',
    minHeight: '12rem',
    transition: 'transform var(--transition-fast)',
  },
  cardHeader: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
  },
  icon: {
    fontSize: '1.5rem',
  },
  cardTitle: {
    fontSize: '1rem',
    fontWeight: '600',
    color: 'var(--text-primary)',
    fontFamily: 'var(--font-display)',
  },
  cardBody: {
    fontSize: '0.85rem',
    color: 'var(--text-secondary)',
    lineHeight: '1.5',
  },
  stepsSection: {
    marginTop: '1rem',
  },
  sectionTitle: {
    fontSize: '1.25rem',
    fontWeight: '700',
    fontFamily: 'var(--font-display)',
    color: 'var(--text-primary)',
  },
  sectionSubtitle: {
    fontSize: '0.85rem',
    color: 'var(--text-secondary)',
    marginBottom: '1.5rem',
  },
  stepsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: '1.25rem',
  },
  stepCard: {
    padding: '1.5rem',
    borderRadius: 'var(--radius-lg)',
    backgroundColor: 'var(--bg-card)',
    border: '1px solid var(--border)',
    display: 'flex',
    flexDirection: 'column',
    gap: '0.75rem',
    position: 'relative',
    transition: 'border-color var(--transition-fast)',
  },
  stepId: {
    fontSize: '2rem',
    fontWeight: '800',
    color: 'var(--accent-blue-light)',
    opacity: 0.8,
    fontFamily: 'var(--font-display)',
  },
  stepTitle: {
    fontSize: '1rem',
    fontWeight: '600',
    color: 'var(--text-primary)',
    fontFamily: 'var(--font-display)',
  },
  stepBody: {
    fontSize: '0.85rem',
    color: 'var(--text-secondary)',
    lineHeight: '1.5',
  },
  helplineCard: {
    padding: '1.5rem 2rem',
    borderRadius: 'var(--radius-lg)',
    backgroundColor: 'var(--bg-surface)',
    border: '1px solid rgba(37, 99, 235, 0.15)',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: '1rem',
  },
  helpLeft: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.25rem',
  },
  helpTitle: {
    fontSize: '1.1rem',
    fontWeight: '700',
    color: 'var(--text-primary)',
    fontFamily: 'var(--font-display)',
  },
  helpText: {
    fontSize: '0.9rem',
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
    textDecoration: 'none',
    boxShadow: '0 4px 12px rgba(37, 99, 235, 0.2)',
    fontFamily: 'var(--font-body)',
  }
};
