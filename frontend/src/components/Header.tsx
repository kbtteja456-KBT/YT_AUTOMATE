import React from 'react';
import { ChevronDownIcon } from './Icons';

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
  const displayName = channelTitle || 'Bhanu Teja';
  const initial = displayName.charAt(0).toUpperCase() || 'B';

  return (
    <header className="top-header">
      <div className="header-left">
        <h2 className="page-title">{title}</h2>
        {zeroCostMode && (
          <div className="zero-cost-badge">
            <span className="zero-cost-dot" />
            <span>Zero-Cost Mode Active (₹0)</span>
          </div>
        )}
      </div>

      <div className="header-right">
        <div className="user-profile-pill" title="Connected Account">
          {channelAvatar ? (
            <img src={channelAvatar} alt={displayName} className="user-avatar-img" />
          ) : (
            <div className="user-avatar-badge">{initial}</div>
          )}
          <span className="user-name-label">{displayName}</span>
          <span className="user-online-dot" />
          <ChevronDownIcon size={12} color="#94a3b8" />
        </div>

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
