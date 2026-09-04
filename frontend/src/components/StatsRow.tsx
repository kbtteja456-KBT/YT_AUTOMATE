import React from 'react';

interface StatsRowProps {
  videosCount: number;
  subscribers?: string | number;
  totalViews?: string | number;
  avgQcScore?: number;
  channelTitle?: string;
}

export const StatsRow: React.FC<StatsRowProps> = ({
  videosCount,
  subscribers = 'NOT AVAILABLE',
  totalViews = 'NOT AVAILABLE',
  avgQcScore = 92.5,
  channelTitle
}) => {
  const formatValue = (val: string | number | undefined) => {
    if (val === undefined || val === null || val === 'NOT AVAILABLE') return 'NOT AVAILABLE';
    if (typeof val === 'number') return val.toLocaleString();
    return val;
  };

  return (
    <div className="stats-grid">
      <div className="card stat-card">
        <div className="stat-header">
          <span>YouTube Subscribers</span>
          <span>👥</span>
        </div>
        <div className="stat-value">{formatValue(subscribers)}</div>
        <div className="stat-meta">
          {channelTitle ? `Channel: ${channelTitle}` : 'Real Data from YouTube API'}
        </div>
      </div>

      <div className="card stat-card">
        <div className="stat-header">
          <span>Total Views</span>
          <span>👁️</span>
        </div>
        <div className="stat-value">{formatValue(totalViews)}</div>
        <div className="stat-meta">
          {channelTitle ? 'Live from YouTube API' : 'YouTube Analytics API'}
        </div>
      </div>

      <div className="card stat-card">
        <div className="stat-header">
          <span>Rendered Videos</span>
          <span>🎬</span>
        </div>
        <div className="stat-value">{videosCount}</div>
        <div className="stat-meta">Local Database State</div>
      </div>

      <div className="card stat-card">
        <div className="stat-header">
          <span>Average QC Score</span>
          <span>⭐</span>
        </div>
        <div className="stat-value">{avgQcScore > 0 ? `${avgQcScore.toFixed(1)}/100` : 'NOT AVAILABLE'}</div>
        <div className="stat-meta">Hard gate minimum: 90/100</div>
      </div>
    </div>
  );
};

