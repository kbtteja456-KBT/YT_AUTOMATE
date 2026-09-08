import React from 'react';

interface TermsPageProps {
  onBack?: () => void;
}

export const TermsPage: React.FC<TermsPageProps> = ({ onBack }) => {
  return (
    <div style={{
      minHeight: '100vh',
      background: 'transparent',
      color: '#e2e8f0',
      fontFamily: "'Plus Jakarta Sans', sans-serif",
      padding: '40px 20px',
      lineHeight: 1.7,
      position: 'relative',
      zIndex: 10,
      overflowY: 'auto'
    }}>
      <div style={{
        maxWidth: '860px',
        margin: '0 auto',
        backgroundColor: 'rgba(15, 20, 28, 0.88)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        border: '1px solid rgba(245, 158, 11, 0.25)',
        borderRadius: '20px',
        padding: '40px',
        boxShadow: '0 24px 64px rgba(0, 0, 0, 0.8), 0 0 32px rgba(245, 158, 11, 0.1)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
          {onBack && (
            <button
              onClick={onBack}
              style={{
                background: 'rgba(245, 158, 11, 0.1)',
                border: '1px solid rgba(245, 158, 11, 0.3)',
                color: '#fbbf24',
                padding: '8px 18px',
                borderRadius: '8px',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '14px'
              }}
            >
              ← Back to Auto YouTube Video Bot
            </button>
          )}

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <img
              src="/favicon.png"
              alt="Logo"
              style={{ width: '32px', height: '32px', borderRadius: '8px', objectFit: 'contain' }}
            />
            <span style={{ fontWeight: 700, color: '#fbbf24', fontSize: '14px' }}>Auto YouTube Video Bot</span>
          </div>
        </div>

        <h1 style={{
          fontFamily: "'Outfit', sans-serif",
          fontSize: '32px',
          fontWeight: 800,
          color: '#ffffff',
          marginBottom: '8px'
        }}>
          Terms of Service
        </h1>
        <p style={{ color: '#94a3b8', marginBottom: '28px', fontSize: '14px' }}>
          Last Updated: March 2026 • Effective for: <strong style={{ color: '#fbbf24' }}>Auto YouTube Video Bot</strong>
        </p>

        <section style={{ marginBottom: '28px' }}>
          <h2 style={{ fontSize: '20px', color: '#fbbf24', borderBottom: '1px solid rgba(245, 158, 11, 0.2)', paddingBottom: '8px' }}>
            1. Acceptance of Terms
          </h2>
          <p>
            By accessing or using <strong>Auto YouTube Video Bot</strong>, you agree to comply with and be bound by these Terms of Service. If you do not agree with any part of these terms, you may not use our services.
          </p>
        </section>

        <section style={{ marginBottom: '28px' }}>
          <h2 style={{ fontSize: '20px', color: '#fbbf24', borderBottom: '1px solid rgba(245, 158, 11, 0.2)', paddingBottom: '8px' }}>
            2. YouTube API Integration & Compliance
          </h2>
          <p>
            Our service integrates directly with YouTube API Services. By using our YouTube integration features, you acknowledge and agree that:
          </p>
          <ul style={{ paddingLeft: '20px' }}>
            <li>
              You are bound by the{' '}
              <a
                href="https://www.youtube.com/t/terms"
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: '#34d399', textDecoration: 'underline' }}
              >
                YouTube Terms of Service
              </a>.
            </li>
            <li>
              You agree to the{' '}
              <a
                href="https://policies.google.com/privacy"
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: '#34d399', textDecoration: 'underline' }}
              >
                Google Privacy Policy
              </a>.
            </li>
            <li>
              You are solely responsible for ensuring that all videos published to your channel comply with YouTube Community Guidelines and Copyright policies.
            </li>
          </ul>
        </section>

        <section style={{ marginBottom: '28px' }}>
          <h2 style={{ fontSize: '20px', color: '#fbbf24', borderBottom: '1px solid rgba(245, 158, 11, 0.2)', paddingBottom: '8px' }}>
            3. User Responsibilities & Content Ownership
          </h2>
          <p>
            You retain 100% ownership of your YouTube channel, your generated videos, and the content published through Auto YouTube Video Bot. You agree not to use the service to generate hate speech, harassment, copyright-infringing content, or misleading spam.
          </p>
        </section>

        <section style={{ marginBottom: '28px' }}>
          <h2 style={{ fontSize: '20px', color: '#fbbf24', borderBottom: '1px solid rgba(245, 158, 11, 0.2)', paddingBottom: '8px' }}>
            4. Service Availability & Modifications
          </h2>
          <p>
            We strive to maintain continuous uptime of the automation pipeline. However, we are not liable for any disruptions caused by third-party API rate limits, YouTube platform maintenance, or external service outages.
          </p>
        </section>

        <section style={{ marginBottom: '28px' }}>
          <h2 style={{ fontSize: '20px', color: '#fbbf24', borderBottom: '1px solid rgba(245, 158, 11, 0.2)', paddingBottom: '8px' }}>
            5. Contact Information
          </h2>
          <p>
            For questions or inquiries regarding these Terms of Service, contact:
          </p>
          <p style={{ backgroundColor: 'rgba(22, 27, 34, 0.9)', border: '1px solid rgba(245, 158, 11, 0.25)', padding: '12px 16px', borderRadius: '8px', display: 'inline-block' }}>
            📧 Support Email: <strong style={{ color: '#fbbf24' }}>kbtteja456@gmail.com</strong>
          </p>
        </section>
      </div>
    </div>
  );
};
