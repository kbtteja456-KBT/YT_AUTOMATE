import React from 'react';

interface PrivacyPageProps {
  onBack?: () => void;
}

export const PrivacyPage: React.FC<PrivacyPageProps> = ({ onBack }) => {
  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#090c10',
      color: '#e6edf3',
      fontFamily: "'Plus Jakarta Sans', sans-serif",
      padding: '40px 20px',
      lineHeight: 1.7
    }}>
      <div style={{
        maxWidth: '860px',
        margin: '0 auto',
        backgroundColor: '#0d1117',
        border: '1px solid #30363d',
        borderRadius: '16px',
        padding: '40px'
      }}>
        {onBack && (
          <button
            onClick={onBack}
            style={{
              background: 'transparent',
              border: '1px solid #30363d',
              color: '#58a6ff',
              padding: '8px 16px',
              borderRadius: '8px',
              cursor: 'pointer',
              marginBottom: '24px',
              fontWeight: 600
            }}
          >
            ← Back to Auto YouTube Video Bot
          </button>
        )}

        <h1 style={{
          fontFamily: "'Outfit', sans-serif",
          fontSize: '32px',
          fontWeight: 800,
          color: '#ffffff',
          marginBottom: '8px'
        }}>
          Privacy Policy
        </h1>
        <p style={{ color: '#8b949e', marginBottom: '28px', fontSize: '14px' }}>
          Last Updated: March 2026 • Effective for: <strong>Auto YouTube Video Bot</strong>
        </p>

        <div style={{
          backgroundColor: 'rgba(56, 139, 253, 0.1)',
          border: '1px solid rgba(56, 139, 253, 0.4)',
          borderRadius: '12px',
          padding: '20px',
          marginBottom: '32px'
        }}>
          <h3 style={{ color: '#58a6ff', margin: '0 0 8px 0', fontSize: '18px' }}>
            YouTube API Services Compliance Notice
          </h3>
          <p style={{ margin: 0, fontSize: '15px' }}>
            <strong>Auto YouTube Video Bot</strong> uses YouTube API Services to authenticate YouTube channel owners, retrieve channel analytics (subscriber count and view metrics), and upload authorized YouTube Shorts videos created by the user. By using Auto YouTube Video Bot, you agree to be bound by the{' '}
            <a
              href="https://www.youtube.com/t/terms"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: '#58a6ff', textDecoration: 'underline' }}
            >
              YouTube Terms of Service
            </a>{' '}
            and the{' '}
            <a
              href="https://policies.google.com/privacy"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: '#58a6ff', textDecoration: 'underline' }}
            >
              Google Privacy Policy
            </a>.
          </p>
        </div>

        <section style={{ marginBottom: '28px' }}>
          <h2 style={{ fontSize: '20px', color: '#ffffff', borderBottom: '1px solid #21262d', paddingBottom: '8px' }}>
            1. Information We Collect
          </h2>
          <p>
            When you use <strong>Auto YouTube Video Bot</strong>, we collect and process the following categories of information:
          </p>
          <ul style={{ paddingLeft: '20px' }}>
            <li><strong>Account & Workspace Credentials:</strong> Email address, name, and hashed credentials used to authenticate your session.</li>
            <li><strong>YouTube Channel Data:</strong> When you voluntarily connect your YouTube channel via Google OAuth 2.0, we access your channel ID, channel title, channel thumbnail, subscriber count, and view metrics using authorized YouTube API scopes (<code>https://www.googleapis.com/auth/youtube.upload</code> and <code>https://www.googleapis.com/auth/youtube.readonly</code>).</li>
            <li><strong>OAuth Access & Refresh Tokens:</strong> Tokens granted by Google to upload videos on your behalf and refresh your connection without requiring repeated logins.</li>
            <li><strong>Content Generation Preferences:</strong> Niche topics, video style settings, and generation history.</li>
          </ul>
        </section>

        <section style={{ marginBottom: '28px' }}>
          <h2 style={{ fontSize: '20px', color: '#ffffff', borderBottom: '1px solid #21262d', paddingBottom: '8px' }}>
            2. How We Use Your Information
          </h2>
          <p>We use the data accessed through the YouTube API strictly to provide core platform functionality:</p>
          <ul style={{ paddingLeft: '20px' }}>
            <li>To display your connected channel profile and live performance metrics (subscribers and views) within your private workspace.</li>
            <li>To render and publish AI-generated YouTube Shorts to your channel according to your configured schedule and automated pipeline.</li>
            <li>To ensure multi-tenant data isolation so no other user or workspace can access your YouTube credentials.</li>
          </ul>
          <p>
            <strong>We DO NOT:</strong>
          </p>
          <ul style={{ paddingLeft: '20px' }}>
            <li>Sell, lease, or rent your personal data or YouTube credentials to any third party.</li>
            <li>Use your YouTube data for advertising or marketing purposes.</li>
            <li>Share your YouTube channel tokens with external AI providers.</li>
          </ul>
        </section>

        <section style={{ marginBottom: '28px' }}>
          <h2 style={{ fontSize: '20px', color: '#ffffff', borderBottom: '1px solid #21262d', paddingBottom: '8px' }}>
            3. Data Storage, Retention & Security
          </h2>
          <p>
            All YouTube OAuth tokens are encrypted at rest in secure databases. Access is strictly scoped to your tenant workspace. Tokens are retained only for as long as your workspace maintains an active connection. If you disconnect your channel or delete your workspace, your stored OAuth tokens and channel metadata are immediately and permanently purged from our database.
          </p>
        </section>

        <section style={{ marginBottom: '28px' }}>
          <h2 style={{ fontSize: '20px', color: '#ffffff', borderBottom: '1px solid #21262d', paddingBottom: '8px' }}>
            4. How to Revoke Access to Your Data
          </h2>
          <p>
            You retain full control over your YouTube channel permissions at all times. You can revoke Auto YouTube Video Bot’s access through any of the following methods:
          </p>
          <ol style={{ paddingLeft: '20px' }}>
            <li>
              <strong>Google Security Settings:</strong> You can revoke access directly via the{' '}
              <a
                href="https://security.google.com/settings/security/permissions"
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: '#58a6ff', textDecoration: 'underline' }}
              >
                Google Security Settings Permissions Page
              </a>.
            </li>
            <li>
              <strong>Inside the App:</strong> Navigate to the Settings tab in your Auto YouTube Video Bot workspace and click <em>"Disconnect Channel"</em>.
            </li>
          </ol>
        </section>

        <section style={{ marginBottom: '28px' }}>
          <h2 style={{ fontSize: '20px', color: '#ffffff', borderBottom: '1px solid #21262d', paddingBottom: '8px' }}>
            5. Contact Us
          </h2>
          <p>
            If you have questions about this Privacy Policy, your data, or wish to request data deletion, please contact the developer at:
          </p>
          <p style={{ backgroundColor: '#161b22', padding: '12px 16px', borderRadius: '8px', display: 'inline-block' }}>
            📧 Support Email: <strong>kbtteja456@gmail.com</strong>
          </p>
        </section>
      </div>
    </div>
  );
};
