import React, { useState } from 'react';
import { api, UserProfile, WorkspaceContext } from '../services/api';
import { PlayIcon, SparklesIcon } from '../components/Icons';

interface AuthPageProps {
  onAuthenticated: (user: UserProfile, workspace: WorkspaceContext) => void;
  onBack?: () => void;
}

export const AuthPage: React.FC<AuthPageProps> = ({ onAuthenticated, onBack }) => {
  const [isRegister, setIsRegister] = useState<boolean>(false);
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [fullName, setFullName] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isRegister) {
        const res = await api.register(email, password, fullName || undefined);
        onAuthenticated(res.user, res.workspace);
      } else {
        const res = await api.login(email, password);
        onAuthenticated(res.user, res.workspace);
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page-wrapper" style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      position: 'relative',
      zIndex: 10,
      padding: '24px'
    }}>
      <div className="auth-card" style={{
        width: '100%',
        maxWidth: '460px',
        background: 'rgba(15, 20, 28, 0.85)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderRadius: '24px',
        border: '1px solid rgba(245, 158, 11, 0.25)',
        boxShadow: '0 24px 64px -12px rgba(0, 0, 0, 0.85), 0 0 32px -4px rgba(245, 158, 11, 0.15)',
        padding: '36px',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {onBack && (
          <button
            onClick={onBack}
            style={{
              background: 'none',
              border: 'none',
              color: '#8b949e',
              cursor: 'pointer',
              fontSize: '13px',
              padding: '0 0 16px 0',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            ← Back to Home
          </button>
        )}

        {/* Subtle Ambient Light Gradient */}
        <div style={{
          position: 'absolute',
          top: '-120px',
          right: '-120px',
          width: '240px',
          height: '240px',
          background: 'radial-gradient(circle, rgba(245, 158, 11, 0.15) 0%, transparent 70%)',
          pointerEvents: 'none'
        }} />

        {/* Brand Header */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div style={{
            width: '64px',
            height: '64px',
            margin: '0 auto 16px auto',
            borderRadius: '18px',
            background: 'linear-gradient(135deg, #ff0033 0%, #cc0000 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 8px 24px rgba(255, 0, 51, 0.35)'
          }}>
            <PlayIcon size={32} color="#ffffff" />
          </div>
          <h1 style={{
            fontSize: '1.75rem',
            fontWeight: 800,
            letterSpacing: '-0.02em',
            background: 'linear-gradient(to right, #f8fafc, #ff3366)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            margin: 0
          }}>
            Auto YouTube Video Bot
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginTop: '6px' }}>
            Autonomous AI YouTube Shorts Publishing Engine
          </p>
        </div>

        {/* Free Trial Pill */}
        <div style={{
          background: 'rgba(16, 185, 129, 0.12)',
          border: '1px solid rgba(16, 185, 129, 0.35)',
          borderRadius: '12px',
          padding: '10px 14px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          marginBottom: '24px'
        }}>
          <SparklesIcon size={18} color="#10b981" />
          <span style={{ fontSize: '0.8125rem', color: '#34d399', fontWeight: 600 }}>
            3 Free Videos Trial Included • Zero Cost Setup
          </span>
        </div>

        {/* Mode Switch Tabs */}
        <div style={{
          display: 'flex',
          background: 'rgba(9, 12, 16, 0.65)',
          padding: '4px',
          borderRadius: '14px',
          marginBottom: '24px',
          border: '1px solid rgba(255, 255, 255, 0.06)'
        }}>
          <button
            type="button"
            onClick={() => { setIsRegister(false); setError(null); }}
            style={{
              flex: 1,
              padding: '10px 16px',
              borderRadius: '10px',
              border: 'none',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '0.875rem',
              transition: 'all 0.2s',
              background: !isRegister ? 'rgba(245, 158, 11, 0.2)' : 'transparent',
              color: !isRegister ? '#f59e0b' : 'var(--text-muted)'
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setIsRegister(true); setError(null); }}
            style={{
              flex: 1,
              padding: '10px 16px',
              borderRadius: '10px',
              border: 'none',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '0.875rem',
              transition: 'all 0.2s',
              background: isRegister ? 'rgba(245, 158, 11, 0.2)' : 'transparent',
              color: isRegister ? '#f59e0b' : 'var(--text-muted)'
            }}
          >
            Create Workspace
          </button>
        </div>

        {error && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.12)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            color: '#f87171',
            borderRadius: '10px',
            padding: '10px 14px',
            fontSize: '0.8125rem',
            marginBottom: '18px'
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {isRegister && (
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '0.8125rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Full Name / Channel Name
              </label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="e.g. Bhanu Teja"
                style={{
                  width: '100%',
                  padding: '12px 14px',
                  background: 'rgba(24, 29, 40, 0.75)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '12px',
                  color: '#fff',
                  fontSize: '0.9375rem',
                  outline: 'none'
                }}
              />
            </div>
          )}

          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Email Address
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@domain.com"
              style={{
                width: '100%',
                padding: '12px 14px',
                background: 'rgba(24, 29, 40, 0.75)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '12px',
                color: '#fff',
                fontSize: '0.9375rem',
                outline: 'none'
              }}
            />
          </div>

          <div style={{ marginBottom: '24px' }}>
            <label style={{ display: 'block', fontSize: '0.8125rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
              Password
            </label>
            <input
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              style={{
                width: '100%',
                padding: '12px 14px',
                background: 'rgba(24, 29, 40, 0.75)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '12px',
                color: '#fff',
                fontSize: '0.9375rem',
                outline: 'none'
              }}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '14px',
              borderRadius: '12px',
              border: 'none',
              background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
              color: '#000',
              fontWeight: 700,
              fontSize: '0.9375rem',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.7 : 1,
              boxShadow: '0 4px 16px rgba(245, 158, 11, 0.35)',
              transition: 'transform 0.15s, opacity 0.15s'
            }}
          >
            {loading ? 'Authenticating...' : isRegister ? 'Launch Free Workspace' : 'Sign In to Dashboard'}
          </button>
        </form>
      </div>
    </div>
  );
};
