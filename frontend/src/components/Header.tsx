import React from 'react';

interface HeaderProps {
  title: string;
  zeroCostMode: boolean;
  channelTitle?: string;
  channelAvatar?: string;
  isGenerating?: boolean;
  onGenerateClick: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  zeroCostMode,
  channelTitle,
  channelAvatar,
  isGenerating,
  onGenerateClick
}) => {
  return (
    <header className="top-header">
      <div className="header-left">
        <h2 className="page-title">{title}</h2>
        {zeroCostMode && (
          <div className="zero-cost-badge">
            <span className="zero-cost-dot"></span>
            <span>Zero-Cost Mode Active (₹0)</span>
          </div>
        )}
      </div>

      <div className="header-right" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {channelTitle && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'rgba(255,255,255,0.05)',
            border: '1px solid rgba(255,255,255,0.1)',
            padding: '5px 12px',
            borderRadius: '20px'
          }}>
            {channelAvatar && (
              <img
                src={channelAvatar}
                alt={channelTitle}
                style={{ width: '22px', height: '22px', borderRadius: '50%' }}
              />
            )}
            <span style={{ fontSize: '13px', fontWeight: 600, color: '#f3f4f6' }}>{channelTitle}</span>
            <span
              title="Channel Connected"
              style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-mint)', display: 'inline-block' }}
            />
          </div>
        )}

        <button className="btn btn-primary" onClick={onGenerateClick} disabled={isGenerating}>
          <span>{isGenerating ? 'Queuing Generation...' : '+ Create Video Now'}</span>
        </button>
      </div>
    </header>
  );
};
