import React from 'react';
import { KeyIcon, SparklesIcon } from './Icons';

interface HeaderProps {
  title: string;
  zeroCostMode?: boolean;
  channelTitle?: string;
  channelAvatar?: string;
  isGenerating?: boolean;
  onGenerateClick: () => void;
  onOpenVault?: () => void;
  trialVideosUsed?: number;
  trialMaxVideos?: number;
  isLegacyOwner?: boolean;
  onLogout?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  zeroCostMode: _zeroCostMode,
  channelTitle,
  channelAvatar,
  isGenerating,
  onGenerateClick,
  onOpenVault,
  trialVideosUsed,
  trialMaxVideos = 3,
  isLegacyOwner = false,
  onLogout
}) => {
  const displayName = channelTitle || (isLegacyOwner ? 'Bhanu Teja (Owner)' : 'My Channel');
  const initial = displayName.charAt(0).toUpperCase() || 'M';

  return (
    <header className="top-header">
      <div className="header-left">
        <h2 className="page-title">{title}</h2>
        {isLegacyOwner ? (
          <div className="zero-cost-badge" style={{ borderColor: 'rgba(245, 158, 11, 0.4)', background: 'rgba(245, 158, 11, 0.1)' }}>
            <span className="zero-cost-dot" style={{ background: '#f59e0b', boxShadow: '0 0 8px #f59e0b' }} />
            <span style={{ color: '#f59e0b', fontWeight: 600 }}>Owner Live Channel</span>
          </div>
        ) : (
          <div
            onClick={onOpenVault}
            title="Click to configure your own API keys"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 10px',
              borderRadius: '8px',
              background: 'rgba(16, 185, 129, 0.12)',
              border: '1px solid rgba(16, 185, 129, 0.35)',
              color: '#34d399',
              fontSize: '0.75rem',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            <SparklesIcon size={12} color="#10b981" />
            <span>Trial: {trialVideosUsed ?? 0}/{trialMaxVideos} Videos</span>
          </div>
        )}
      </div>

      <div className="header-right">
        {onOpenVault && (
          <button
            onClick={onOpenVault}
            title="Open BYOK API Key Vault"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'rgba(245, 158, 11, 0.15)',
              border: '1px solid rgba(245, 158, 11, 0.35)',
              color: '#f59e0b',
              padding: '8px 14px',
              borderRadius: '10px',
              fontSize: '0.8125rem',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            <KeyIcon size={14} />
            <span>API Vault</span>
          </button>
        )}

        <div className="user-profile-pill" title="Connected Account">
          {channelAvatar ? (
            <img src={channelAvatar} alt={displayName} className="user-avatar-img" />
          ) : (
            <div className="user-avatar-badge">{initial}</div>
          )}
          <span className="user-name-label">{displayName}</span>
          <span className="user-online-dot" />
        </div>

        {onLogout && (
          <button
            onClick={onLogout}
            title="Sign out of current workspace"
            style={{
              background: 'rgba(255, 255, 255, 0.06)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              color: 'var(--text-secondary)',
              padding: '8px 12px',
              borderRadius: '10px',
              fontSize: '0.75rem',
              cursor: 'pointer'
            }}
          >
            Logout
          </button>
        )}

        <button
          className="btn btn-primary"
          onClick={onGenerateClick}
          disabled={isGenerating}
        >
          <span>{isGenerating ? 'Queuing Generation...' : '+ Create Video Now'}</span>
        </button>
      </div>
    </header>
  );
};
