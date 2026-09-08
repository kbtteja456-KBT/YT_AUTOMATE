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
      width: '100%',
      minHeight: '100vh',
      background: 'transparent',
      color: '#e6edf3',
      fontFamily: "'Plus Jakarta Sans', sans-serif",
      position: 'relative',
      zIndex: 10,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      boxSizing: 'border-box',
      overflowX: 'hidden'
    }}>
      {/* 1. NAVBAR - Horizontally Centered Container */}
      <header style={{
        width: '100%',
        display: 'flex',
        justifyContent: 'center',
        position: 'sticky',
        top: 0,
        zIndex: 50,
        padding: '16px 0',
        boxSizing: 'border-box'
      }}>
        <nav style={{
          width: 'min(100% - 32px, 1200px)',
          margin: '0 auto',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '16px',
          padding: '12px 24px',
          borderRadius: '16px',
          border: '1px solid rgba(245, 158, 11, 0.22)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          backgroundColor: 'rgba(15, 20, 28, 0.48)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.45)',
          boxSizing: 'border-box'
        }}>
          {/* Brand Identity */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <img
              src="/favicon.png"
              alt="Auto YouTube Video Bot Logo"
              style={{
                width: '38px',
                height: '38px',
                borderRadius: '10px',
                objectFit: 'contain',
                boxShadow: '0 0 16px rgba(245, 158, 11, 0.4)',
                border: '1px solid rgba(245, 158, 11, 0.3)'
              }}
            />
            <div>
              <h1 style={{
                fontFamily: "'Outfit', sans-serif",
                fontSize: '18px',
                fontWeight: 800,
                letterSpacing: '-0.3px',
                margin: 0,
                background: 'linear-gradient(to right, #ffffff, #fbbf24)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                lineHeight: 1.2
              }}>
                Auto YouTube Video Bot
              </h1>
              <span style={{ fontSize: '10px', color: '#34d399', textTransform: 'uppercase', letterSpacing: '0.8px', fontWeight: 600 }}>
                AI Video Synthesis Engine
              </span>
            </div>
          </div>

          {/* Navigation Links & CTA */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px', flexWrap: 'wrap' }}>
            <a
              href="#purpose"
              style={{
                color: '#fbbf24',
                textDecoration: 'none',
                fontSize: '13px',
                fontWeight: 600,
                transition: 'color 0.2s'
              }}
            >
              App Purpose
            </a>
            <button
              onClick={onPrivacyClick}
              style={{
                background: 'none',
                border: 'none',
                color: '#94a3b8',
                cursor: 'pointer',
                fontSize: '13px',
                fontWeight: 500,
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
                color: '#94a3b8',
                cursor: 'pointer',
                fontSize: '13px',
                fontWeight: 500,
                transition: 'color 0.2s'
              }}
            >
              Terms
            </button>
            <button
              onClick={onLoginClick}
              style={{
                background: 'linear-gradient(135deg, #f59e0b 0%, #10b981 100%)',
                color: '#090c10',
                border: 'none',
                borderRadius: '8px',
                padding: '9px 20px',
                fontWeight: 800,
                fontSize: '13px',
                cursor: 'pointer',
                boxShadow: '0 4px 16px rgba(245, 158, 11, 0.35)',
                transition: 'transform 0.15s, box-shadow 0.15s'
              }}
            >
              Sign In / Register
            </button>
          </div>
        </nav>
      </header>

      {/* 2. HERO SECTION - Perfectly Centered in Viewport */}
      <section style={{
        width: '100%',
        display: 'flex',
        justifyContent: 'center',
        margin: '28px 0 40px 0',
        boxSizing: 'border-box'
      }}>
        <div style={{
          width: 'min(100% - 32px, 1200px)',
          margin: '0 auto',
          backgroundColor: 'rgba(15, 20, 28, 0.45)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          border: '1px solid rgba(245, 158, 11, 0.28)',
          borderRadius: '24px',
          padding: 'clamp(36px, 5vw, 56px) clamp(20px, 4vw, 48px)',
          textAlign: 'center',
          boxShadow: '0 24px 64px rgba(0, 0, 0, 0.55), 0 0 32px rgba(245, 158, 11, 0.08)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          boxSizing: 'border-box'
        }}>
          {/* Compliance Badge */}
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            backgroundColor: 'rgba(245, 158, 11, 0.12)',
            border: '1px solid rgba(245, 158, 11, 0.35)',
            borderRadius: '999px',
            padding: '6px 20px',
            fontSize: '13px',
            fontWeight: 600,
            color: '#fbbf24',
            marginBottom: '24px',
            maxWidth: '100%',
            textAlign: 'center'
          }}>
            <span>⚡</span>
            <span>Official YouTube API Services Developer Compliance</span>
          </div>

          {/* Centered Main Heading */}
          <h2 style={{
            fontFamily: "'Outfit', sans-serif",
            fontSize: 'clamp(28px, 4.2vw, 46px)',
            lineHeight: 1.22,
            fontWeight: 800,
            letterSpacing: '-1px',
            background: 'linear-gradient(135deg, #ffffff 20%, #fbbf24 65%, #34d399 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            margin: '0 auto 20px auto',
            maxWidth: '860px',
            textAlign: 'center'
          }}>
            Autonomous YouTube Shorts Creation &amp; Scheduled Publishing
          </h2>

          {/* Centered Description */}
          <p style={{
            fontSize: '16px',
            color: '#cbd5e1',
            maxWidth: '720px',
            margin: '0 auto 36px auto',
            lineHeight: 1.7,
            textAlign: 'center'
          }}>
            <strong style={{ color: '#fbbf24' }}>Auto YouTube Video Bot</strong> is a creator automation suite that connects securely to your authorized YouTube channel, creates high-retention vertical short videos using intelligent multi-agent scripting, voice synthesis, and dynamic media rendering, and publishes on your automated schedule.
          </p>

          {/* Symmetrically Centered Action Buttons */}
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            gap: '16px',
            flexWrap: 'wrap'
          }}>
            <button
              onClick={onLoginClick}
              style={{
                background: 'linear-gradient(135deg, #f59e0b 0%, #10b981 100%)',
                color: '#090c10',
                border: 'none',
                borderRadius: '12px',
                padding: '14px 34px',
                fontSize: '15px',
                fontWeight: 800,
                cursor: 'pointer',
                boxShadow: '0 6px 24px rgba(245, 158, 11, 0.45)',
                transition: 'transform 0.15s, box-shadow 0.15s'
              }}
            >
              Get Started Free →
            </button>
            <a
              href="#purpose"
              style={{
                background: 'rgba(16, 185, 129, 0.12)',
                border: '1px solid rgba(16, 185, 129, 0.35)',
                color: '#34d399',
                borderRadius: '12px',
                padding: '14px 28px',
                fontSize: '15px',
                fontWeight: 600,
                textDecoration: 'none',
                display: 'inline-flex',
                alignItems: 'center'
              }}
            >
              Learn App Purpose
            </a>
          </div>
        </div>
      </section>

      {/* 3. ABOUT THIS APPLICATION SECTION - Identical Horizontal Alignment */}
      <section id="purpose" style={{
        width: '100%',
        display: 'flex',
        justifyContent: 'center',
        marginBottom: '40px',
        boxSizing: 'border-box'
      }}>
        <div style={{
          width: 'min(100% - 32px, 1200px)',
          margin: '0 auto',
          backgroundColor: 'rgba(15, 20, 28, 0.48)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          border: '1px solid rgba(245, 158, 11, 0.25)',
          borderRadius: '24px',
          padding: 'clamp(28px, 4vw, 44px) clamp(20px, 4vw, 40px)',
          boxShadow: '0 16px 48px rgba(0, 0, 0, 0.5), 0 0 24px rgba(245, 158, 11, 0.08)',
          boxSizing: 'border-box'
        }}>
          <div style={{
            display: 'inline-block',
            backgroundColor: 'rgba(16, 185, 129, 0.15)',
            color: '#34d399',
            fontSize: '12px',
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '1px',
            padding: '4px 12px',
            borderRadius: '6px',
            marginBottom: '16px'
          }}>
            About This Application
          </div>
          <h2 style={{
            fontFamily: "'Outfit', sans-serif",
            fontSize: '30px',
            fontWeight: 800,
            color: '#ffffff',
            marginBottom: '16px'
          }}>
            Purpose of Auto YouTube Video Bot
          </h2>
          <p style={{ fontSize: '15px', color: '#cbd5e1', lineHeight: 1.7, marginBottom: '20px' }}>
            <strong style={{ color: '#fbbf24' }}>Auto YouTube Video Bot</strong> is designed for independent video creators, educators, and digital marketers seeking to automate repetitive video editing and publishing workflows. Producing consistent, high-quality vertical video shorts requires multiple disconnected steps: script writing, voiceover recording, subtitle synchronization, stock media sourcing, and video rendering.
          </p>
          <p style={{ fontSize: '15px', color: '#cbd5e1', lineHeight: 1.7, marginBottom: '28px' }}>
            Our application solves this problem by providing a unified, multi-agent AI pipeline that handles the creative assembly of short videos and uses the official YouTube Data API v3 to upload them directly to the user's verified YouTube channel according to their custom publishing schedule.
          </p>

          <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#fbbf24', marginBottom: '16px' }}>
            Why Auto YouTube Video Bot Requests YouTube API Access:
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginBottom: '24px' }}>
            <div style={{ backgroundColor: 'rgba(22, 27, 34, 0.5)', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)', padding: '20px', borderRadius: '12px', border: '1px solid rgba(245, 158, 11, 0.2)' }}>
              <h4 style={{ color: '#fbbf24', margin: '0 0 8px 0', fontSize: '15px' }}>1. Automated Video Publishing</h4>
              <p style={{ fontSize: '13px', color: '#94a3b8', margin: 0, lineHeight: 1.6 }}>
                Uses the <code style={{ color: '#34d399' }}>youtube.upload</code> scope to upload user-approved video files directly to the user's connected YouTube channel without requiring manual file downloads and re-uploads.
              </p>
            </div>
            <div style={{ backgroundColor: 'rgba(22, 27, 34, 0.5)', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)', padding: '20px', borderRadius: '12px', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
              <h4 style={{ color: '#34d399', margin: '0 0 8px 0', fontSize: '15px' }}>2. Channel Verification & Analytics</h4>
              <p style={{ fontSize: '13px', color: '#94a3b8', margin: 0, lineHeight: 1.6 }}>
                Uses the <code style={{ color: '#fbbf24' }}>youtube.readonly</code> scope to confirm channel identity and display recent subscriber counts and view analytics in the creator's private workspace dashboard.
              </p>
            </div>
          </div>

          <div style={{
            backgroundColor: 'rgba(245, 158, 11, 0.08)',
            border: '1px solid rgba(245, 158, 11, 0.25)',
            borderRadius: '12px',
            padding: '16px 20px',
            fontSize: '13px',
            color: '#e2e8f0',
            lineHeight: 1.6
          }}>
            <strong style={{ color: '#fbbf24' }}>Google API Services User Data Policy Compliance:</strong> Auto YouTube Video Bot's use and transfer to any other app of information received from Google APIs adheres to the{' '}
            <a
              href="https://developers.google.com/terms/api-services-user-data-policy"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: '#fbbf24', textDecoration: 'underline' }}
            >
              Google API Services User Data Policy
            </a>, including the Limited Use requirements.
          </div>
        </div>
      </section>

      {/* 4. FEATURE PILLARS - Identical Width & Alignment */}
      <section style={{
        width: '100%',
        display: 'flex',
        justifyContent: 'center',
        marginBottom: '60px',
        boxSizing: 'border-box'
      }}>
        <div style={{
          width: 'min(100% - 32px, 1200px)',
          margin: '0 auto',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '20px',
          boxSizing: 'border-box'
        }}>
          <div style={{
            backgroundColor: 'rgba(15, 20, 28, 0.45)',
            backdropFilter: 'blur(16px)',
            WebkitBackdropFilter: 'blur(16px)',
            border: '1px solid rgba(245, 158, 11, 0.2)',
            borderRadius: '16px',
            padding: '28px'
          }}>
            <div style={{ fontSize: '28px', marginBottom: '14px' }}>🚀</div>
            <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#fbbf24', marginBottom: '10px' }}>
              Direct YouTube Uploads
            </h3>
            <p style={{ fontSize: '13px', color: '#94a3b8', margin: 0, lineHeight: 1.6 }}>
              Seamlessly publish 1080x1920 vertical shorts directly to your connected YouTube channel using authorized YouTube API Services.
            </p>
          </div>

          <div style={{
            backgroundColor: 'rgba(15, 20, 28, 0.45)',
            backdropFilter: 'blur(16px)',
            WebkitBackdropFilter: 'blur(16px)',
            border: '1px solid rgba(16, 185, 129, 0.2)',
            borderRadius: '16px',
            padding: '28px'
          }}>
            <div style={{ fontSize: '28px', marginBottom: '14px' }}>📊</div>
            <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#34d399', marginBottom: '10px' }}>
              Real-Time Channel Analytics
            </h3>
            <p style={{ fontSize: '13px', color: '#94a3b8', margin: 0, lineHeight: 1.6 }}>
              Live channel subscriber count, views, and video performance metrics monitored directly from your personal workspace.
            </p>
          </div>

          <div style={{
            backgroundColor: 'rgba(15, 20, 28, 0.45)',
            backdropFilter: 'blur(16px)',
            WebkitBackdropFilter: 'blur(16px)',
            border: '1px solid rgba(245, 158, 11, 0.2)',
            borderRadius: '16px',
            padding: '28px'
          }}>
            <div style={{ fontSize: '28px', marginBottom: '14px' }}>🛡️</div>
            <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#fbbf24', marginBottom: '10px' }}>
              Enterprise Workspace Isolation
            </h3>
            <p style={{ fontSize: '13px', color: '#94a3b8', margin: 0, lineHeight: 1.6 }}>
              Multi-tenant data isolation ensures your tokens, keys, and media remain strictly separated and protected with zero data sharing.
            </p>
          </div>
        </div>
      </section>

      {/* 5. FOOTER - Centered Matching Container */}
      <footer style={{
        width: '100%',
        borderTop: '1px solid rgba(245, 158, 11, 0.15)',
        padding: '36px 0',
        backgroundColor: 'rgba(9, 12, 16, 0.55)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        display: 'flex',
        justifyContent: 'center',
        boxSizing: 'border-box'
      }}>
        <div style={{
          width: 'min(100% - 32px, 1200px)',
          margin: '0 auto',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
          boxSizing: 'border-box',
          padding: '0 12px'
        }}>
          <div style={{ fontSize: '13px', color: '#8b949e' }}>
            © 2026 <strong style={{ color: '#fbbf24' }}>Auto YouTube Video Bot</strong>. All rights reserved.
          </div>
          <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
            <button
              onClick={onPrivacyClick}
              style={{ background: 'none', border: 'none', color: '#fbbf24', cursor: 'pointer', fontSize: '13px', fontWeight: 500 }}
            >
              Privacy Policy
            </button>
            <button
              onClick={onTermsClick}
              style={{ background: 'none', border: 'none', color: '#34d399', cursor: 'pointer', fontSize: '13px', fontWeight: 500 }}
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
