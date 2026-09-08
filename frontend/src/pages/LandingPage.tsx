import React from 'react';

interface LandingPageProps {
  onLoginClick: () => void;
  onPrivacyClick: () => void;
  onTermsClick: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({
  onLoginClick,
  onPrivacyClick,
  onTermsClick,
}) => {
  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#090c10',
      color: '#e6edf3',
      fontFamily: "'Plus Jakarta Sans', sans-serif",
      position: 'relative',
      overflowX: 'hidden'
    }}>
      {/* Top Navigation */}
      <nav style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '20px 48px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        backdropFilter: 'blur(12px)',
        backgroundColor: 'rgba(9, 12, 16, 0.75)',
        position: 'sticky',
        top: 0,
        zIndex: 50
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #ff0033 0%, #cc0000 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 16px rgba(255, 0, 51, 0.4)'
          }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="#ffffff">
              <path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zm-10.615 12.816v-8l8 3.993-8 4.007z" />
            </svg>
          </div>
          <div>
            <h1 style={{
              fontFamily: "'Outfit', sans-serif",
              fontSize: '20px',
              fontWeight: 800,
              letterSpacing: '-0.5px',
              margin: 0,
              color: '#ffffff'
            }}>
              Auto YouTube Video Bot
            </h1>
            <span style={{ fontSize: '11px', color: '#8b949e', textTransform: 'uppercase', letterSpacing: '1px' }}>
              Autonomous Shorts Engine
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
          <button
            onClick={onPrivacyClick}
            style={{
              background: 'none',
              border: 'none',
              color: '#8b949e',
              cursor: 'pointer',
              fontSize: '14px',
              transition: 'color 0.2s'
            }}
          >
            Privacy Policy
          </button>
          <button
            onClick={onTermsClick}
            style={{
              background: 'none',
              border: 'none',
              color: '#8b949e',
              cursor: 'pointer',
              fontSize: '14px',
              transition: 'color 0.2s'
            }}
          >
            Terms
          </button>
          <button
            onClick={onLoginClick}
            style={{
              background: 'linear-gradient(135deg, #ff0033 0%, #ff3366 100%)',
              color: '#ffffff',
              border: 'none',
              borderRadius: '8px',
              padding: '10px 22px',
              fontWeight: 600,
              fontSize: '14px',
              cursor: 'pointer',
              boxShadow: '0 4px 14px rgba(255, 0, 51, 0.35)',
              transition: 'transform 0.15s, box-shadow 0.15s'
            }}
          >
            Sign In / Register
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <section style={{
        maxWidth: '1100px',
        margin: '0 auto',
        padding: '80px 24px 60px',
        textAlign: 'center'
      }}>
        <div style={{
          display: 'inline-block',
          backgroundColor: 'rgba(255, 0, 51, 0.12)',
          border: '1px solid rgba(255, 0, 51, 0.3)',
          borderRadius: '999px',
          padding: '6px 18px',
          fontSize: '13px',
          fontWeight: 600,
          color: '#ff4d6d',
          marginBottom: '24px'
        }}>
          ⚡ Official YouTube API Integrated Automation
        </div>

        <h2 style={{
          fontFamily: "'Outfit', sans-serif",
          fontSize: '54px',
          lineHeight: 1.15,
          fontWeight: 800,
          letterSpacing: '-1.5px',
          color: '#ffffff',
          marginBottom: '20px'
        }}>
          Autonomous YouTube Shorts Creation & Scheduled Publishing
        </h2>

        <p style={{
          fontSize: '18px',
          color: '#8b949e',
          maxWidth: '780px',
          margin: '0 auto 36px',
          lineHeight: 1.6
        }}>
          <strong>Auto YouTube Video Bot</strong> connects securely to your authorized YouTube channel, creates high-retention vertical short videos using intelligent multi-agent scripting, voice synthesis, and dynamic media rendering, and publishes on your automated schedule.
        </p>

        <div style={{ display: 'flex', justifyContent: 'center', gap: '16px', marginBottom: '48px' }}>
          <button
            onClick={onLoginClick}
            style={{
              background: 'linear-gradient(135deg, #ff0033 0%, #ff3366 100%)',
              color: '#ffffff',
              border: 'none',
              borderRadius: '10px',
              padding: '16px 36px',
              fontSize: '16px',
              fontWeight: 700,
              cursor: 'pointer',
              boxShadow: '0 6px 24px rgba(255, 0, 51, 0.45)'
            }}
          >
            Get Started Free →
          </button>
          <button
            onClick={onPrivacyClick}
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              color: '#e6edf3',
              borderRadius: '10px',
              padding: '16px 28px',
              fontSize: '16px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            View Privacy Policy
          </button>
        </div>

        {/* YouTube API Disclosure Callout */}
        <div style={{
          backgroundColor: '#0d1117',
          border: '1px solid #30363d',
          borderRadius: '14px',
          padding: '24px',
          textAlign: 'left',
          maxWidth: '820px',
          margin: '0 auto',
          boxShadow: '0 12px 36px rgba(0, 0, 0, 0.4)'
        }}>
          <h4 style={{ margin: '0 0 8px 0', color: '#58a6ff', fontSize: '16px' }}>
            🔒 Official YouTube API Services Developer Disclosure
          </h4>
          <p style={{ margin: 0, fontSize: '14px', color: '#c9d1d9', lineHeight: 1.6 }}>
            Auto YouTube Video Bot connects to YouTube via Google OAuth 2.0 with minimal required permissions (<code>youtube.upload</code> and <code>youtube.readonly</code>). We access channel metadata only to render your workspace dashboard metrics and publish your scheduled Shorts. We never access private messages, personal history, or unrelated account information.
          </p>
        </div>
      </section>

      {/* Feature Pillars */}
      <section style={{
        maxWidth: '1100px',
        margin: '0 auto',
        padding: '40px 24px 80px',
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '24px'
      }}>
        <div style={{
          backgroundColor: '#0d1117',
          border: '1px solid #21262d',
          borderRadius: '16px',
          padding: '32px',
          transition: 'border-color 0.2s'
        }}>
          <div style={{ fontSize: '32px', marginBottom: '16px' }}>🚀</div>
          <h3 style={{ fontSize: '20px', fontWeight: 700, color: '#ffffff', marginBottom: '12px' }}>
            Direct YouTube Uploads
          </h3>
          <p style={{ fontSize: '14px', color: '#8b949e', margin: 0, lineHeight: 1.6 }}>
            Seamlessly publish 1080x1920 vertical shorts directly to your connected YouTube channel using authorized YouTube API Services.
          </p>
        </div>

        <div style={{
          backgroundColor: '#0d1117',
          border: '1px solid #21262d',
          borderRadius: '16px',
          padding: '32px'
        }}>
          <div style={{ fontSize: '32px', marginBottom: '16px' }}>📊</div>
          <h3 style={{ fontSize: '20px', fontWeight: 700, color: '#ffffff', marginBottom: '12px' }}>
            Real-Time Channel Analytics
          </h3>
          <p style={{ fontSize: '14px', color: '#8b949e', margin: 0, lineHeight: 1.6 }}>
            Live channel subscriber count, views, and video performance metrics monitored directly from your personal workspace.
          </p>
        </div>

        <div style={{
          backgroundColor: '#0d1117',
          border: '1px solid #21262d',
          borderRadius: '16px',
          padding: '32px'
        }}>
          <div style={{ fontSize: '32px', marginBottom: '16px' }}>🛡️</div>
          <h3 style={{ fontSize: '20px', fontWeight: 700, color: '#ffffff', marginBottom: '12px' }}>
            Enterprise Workspace Isolation
          </h3>
          <p style={{ fontSize: '14px', color: '#8b949e', margin: 0, lineHeight: 1.6 }}>
            Multi-tenant data isolation ensures your tokens, keys, and media remain strictly separated and protected with zero data sharing.
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid rgba(255, 255, 255, 0.08)',
        padding: '40px 48px',
        backgroundColor: '#07090d',
        fontSize: '13px',
        color: '#8b949e'
      }}>
        <div style={{
          maxWidth: '1100px',
          margin: '0 auto',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px'
        }}>
          <div>
            © 2026 <strong>Auto YouTube Video Bot</strong>. All rights reserved.
          </div>
          <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
            <button
              onClick={onPrivacyClick}
              style={{ background: 'none', border: 'none', color: '#58a6ff', cursor: 'pointer', fontSize: '13px' }}
            >
              Privacy Policy
            </button>
            <button
              onClick={onTermsClick}
              style={{ background: 'none', border: 'none', color: '#58a6ff', cursor: 'pointer', fontSize: '13px' }}
            >
              Terms of Service
            </button>
            <a
              href="https://www.youtube.com/t/terms"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: '#8b949e', textDecoration: 'none' }}
            >
              YouTube Terms of Service
            </a>
            <a
              href="https://policies.google.com/privacy"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: '#8b949e', textDecoration: 'none' }}
            >
              Google Privacy Policy
            </a>
            <a
              href="https://security.google.com/settings/security/permissions"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: '#8b949e', textDecoration: 'none' }}
            >
              Revoke Google Access
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
};
