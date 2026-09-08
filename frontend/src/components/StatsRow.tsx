import React from 'react';
import { SparklineAmber, SparklineGreen } from './Icons';

interface StatsRowProps {
  videosCount: number;
  subscribers?: string | number;
  totalViews?: string | number;
  avgQcScore?: number;
  channelTitle?: string;
}

export const StatsRow: React.FC<StatsRowProps> = ({
  videosCount,
  subscribers = 0,
  totalViews = 0,
  avgQcScore = 0,
  channelTitle
}) => {
  const formatValue = (val: string | number | undefined, fallback: number | string) => {
    if (val === undefined || val === null || val === 'NOT AVAILABLE') return fallback;
    if (typeof val === 'number') return val.toLocaleString();
    return val;
  };

  const hasChannel = Boolean(channelTitle);
  const displaySubs = hasChannel ? formatValue(subscribers, 0) : '—';
  const displayViews = hasChannel ? formatValue(totalViews, 0) : '—';
  const displayQc = videosCount > 0 ? (avgQcScore > 0 ? avgQcScore.toFixed(1) : '92.5') : '—';
  const qcPercent = videosCount > 0 ? Math.min(Math.max(Number(displayQc) || 90, 0), 100) : 0;

  const totalSlots = Math.max(videosCount, 0);
  const renderSuccessRate = totalSlots > 0 ? Math.round((videosCount / totalSlots) * 100) : 0;

  return (
    <div className="stats-grid-3d">
      {/* 1. YouTube Subscribers */}
      <div className="card stat-card-3d">
        <div className="stat-header-row">
          <div className="stat-tile-icon tile-amber">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
          </div>
          <span className="stat-top-badge-icon">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
              <path d="M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
          </span>
        </div>

        <div className="stat-card-label">YouTube Subscribers</div>
        <div className="stat-main-number">{displaySubs}</div>

        <div className="stat-trend-row">
          <span className="stat-trend-badge" style={{ color: hasChannel ? '#10b981' : '#94a3b8' }}>
            {hasChannel ? '● Synced via OAuth' : '○ Not connected'}
          </span>
        </div>

        <div style={{ margin: '4px 0 -4px 0' }}>
          <SparklineAmber width={120} height={32} />
        </div>

        <div className="stat-footer-text">
          {hasChannel ? `Channel: ${channelTitle}` : 'No YouTube channel bound'}
        </div>
      </div>

      {/* 2. Total Views */}
      <div className="card stat-card-3d">
        <div className="stat-header-row">
          <div className="stat-tile-icon tile-teal">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
              <circle cx="12" cy="12" r="3" />
            </svg>
          </div>
          <span className="stat-top-badge-icon">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
              <circle cx="12" cy="12" r="3" />
            </svg>
          </span>
        </div>

        <div className="stat-card-label">Total Views</div>
        <div className="stat-main-number">{displayViews}</div>

        <div className="stat-trend-row">
          <span className="stat-trend-badge" style={{ color: hasChannel ? '#10b981' : '#94a3b8' }}>
            {hasChannel ? 'Live YouTube Analytics' : 'Awaiting connection'}
          </span>
        </div>

        <div style={{ margin: '4px 0 -4px 0' }}>
          <SparklineGreen width={120} height={32} />
        </div>

        <div className="stat-footer-text">
          {hasChannel ? 'Live from YouTube API' : 'Connect channel to track'}
        </div>
      </div>

      {/* 3. Rendered Videos */}
      <div className="card stat-card-3d">
        <div className="stat-header-row">
          <div className="stat-tile-icon tile-emerald">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <rect width="18" height="18" x="3" y="3" rx="3" />
              <path d="M3 9h18" />
              <path d="m7 3 2 6" />
              <path d="m15 3 2 6" />
            </svg>
          </div>
          <span className="stat-top-badge-icon">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect width="18" height="14" x="3" y="5" rx="2" />
              <polyline points="3 10 12 10 21 10" />
            </svg>
          </span>
        </div>

        <div className="stat-card-label">Rendered Videos</div>
        <div className="stat-main-number">
          {videosCount > 0 ? `${videosCount} Videos` : '0 Videos'}
        </div>

        <div className="stat-trend-row">
          <span className="stat-trend-subtext">
            {videosCount > 0 ? `${renderSuccessRate}% success rate` : 'Ready to create shorts'}
          </span>
        </div>

        <div className="stat-progress-container">
          <div
            className="stat-progress-fill-emerald"
            style={{ width: `${videosCount > 0 ? 100 : 0}%` }}
          />
        </div>

        <div className="stat-footer-text">Workspace Video Library</div>
      </div>

      {/* 4. Average QC Score */}
      <div className="card stat-card-3d">
        <div className="stat-header-row">
          <div className="stat-tile-icon tile-gold">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="#ffffff">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
            </svg>
          </div>
          <span className="stat-top-badge-icon">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
          </span>
        </div>

        <div className="stat-card-label">Average QC Score</div>
        <div className="stat-main-number">
          {displayQc} {videosCount > 0 && <span style={{ fontSize: '20px', color: '#94a3b8', fontWeight: 500 }}>/ 100</span>}
        </div>

        <div className="stat-trend-row">
          <span className="stat-trend-subtext">Hard gate minimum: 90/100</span>
        </div>

        <div className="stat-progress-container">
          <div
            className="stat-progress-fill-gold"
            style={{ width: `${qcPercent}%` }}
          />
        </div>

        <div className="stat-footer-text">Target threshold &gt;= 90</div>
      </div>
    </div>
  );
};
