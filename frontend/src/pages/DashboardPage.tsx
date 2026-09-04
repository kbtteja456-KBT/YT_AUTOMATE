import React from 'react';
import { AutopilotHero } from '../components/AutopilotHero';
import { StatsRow } from '../components/StatsRow';
import { ActivityFeed } from '../components/ActivityFeed';
import { AutopilotStatusResponse, ActivityEventItem, VideoItem, ChannelInfo, api } from '../services/api';

interface DashboardPageProps {
  autopilotStatus: AutopilotStatusResponse | null;
  activityEvents: ActivityEventItem[];
  videos: VideoItem[];
  channelInfo: ChannelInfo | null;
  onToggleAutopilot: () => void;
  onGenerateClick: () => void;
  onRefreshData?: () => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  autopilotStatus,
  activityEvents,
  videos,
  channelInfo,
  onToggleAutopilot,
  onGenerateClick,
  onRefreshData
}) => {
  const [isSyncing, setIsSyncing] = React.useState(false);
  const [syncNotice, setSyncNotice] = React.useState<string | null>(null);

  const channel = channelInfo?.is_connected ? channelInfo.channel : null;

  const handleSync = async () => {
    setIsSyncing(true);
    setSyncNotice(null);
    try {
      const res = await api.syncChannel();
      setSyncNotice(res.message || 'Stats synced successfully!');
      if (onRefreshData) onRefreshData();
    } catch (err: any) {
      if (err.message?.includes('re-authentication') || err.message?.includes('401')) {
        try {
          const authUrl = await api.getConnectUrl();
          window.open(authUrl, '_blank');
          setSyncNotice('Authorization window opened. Please click Allow in Google, then click Sync again.');
        } catch {
          setSyncNotice('Re-authentication required. Please connect via Settings.');
        }
      } else {
        setSyncNotice(`Sync note: ${err.message}`);
      }
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <div className="page-body">
      {channel ? (
        <div className="card" style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
          background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(15, 23, 42, 0.6) 100%)',
          border: '1px solid rgba(16, 185, 129, 0.25)',
          padding: '14px 20px',
          borderRadius: 'var(--radius-md)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
              {channel.thumbnail_url ? (
                <img
                  src={channel.thumbnail_url}
                  alt={channel.title}
                  style={{
                    width: '46px',
                    height: '46px',
                    borderRadius: '50%',
                    border: '2px solid var(--accent-mint)',
                    boxShadow: '0 0 12px rgba(16, 185, 129, 0.3)'
                  }}
                />
              ) : (
                <div style={{
                  width: '46px',
                  height: '46px',
                  borderRadius: '50%',
                  background: 'var(--accent-mint)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '20px',
                  fontWeight: 700,
                  color: '#0f172a'
                }}>
                  {channel.title.charAt(0)}
                </div>
              )}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '16px', fontWeight: 700, color: '#f3f4f6' }}>{channel.title}</span>
                  {channel.custom_url && (
                    <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{channel.custom_url}</span>
                  )}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                  Channel ID: <code style={{ color: 'var(--text-muted)' }}>{channel.channel_id}</code>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '4px 10px',
                borderRadius: '12px',
                fontSize: '12px',
                fontWeight: 600,
                background: 'rgba(16, 185, 129, 0.15)',
                color: 'var(--accent-mint)',
                border: '1px solid rgba(16, 185, 129, 0.3)'
              }}>
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent-mint)' }} />
                YouTube Connected
              </span>

              <button
                className="btn btn-secondary"
                onClick={handleSync}
                disabled={isSyncing}
                style={{
                  padding: '6px 14px',
                  fontSize: '13px',
                  background: 'rgba(255, 255, 255, 0.08)',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  cursor: isSyncing ? 'not-allowed' : 'pointer'
                }}
              >
                {isSyncing ? '↻ Syncing with YouTube...' : '↻ Sync Stats'}
              </button>
            </div>
          </div>

          {syncNotice && (
            <div style={{
              fontSize: '12px',
              padding: '6px 12px',
              borderRadius: '6px',
              background: syncNotice.includes('Authorization') ? 'rgba(59, 130, 246, 0.1)' : 'rgba(16, 185, 129, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              color: '#93c5fd'
            }}>
              ℹ️ {syncNotice}
            </div>
          )}
        </div>
      ) : (
        <div className="card" style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'rgba(239, 68, 68, 0.05)',
          border: '1px solid rgba(239, 68, 68, 0.2)',
          padding: '12px 18px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span>⚠️</span>
            <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
              YouTube Channel Not Connected.
            </span>
          </div>
        </div>
      )}

      <AutopilotHero status={autopilotStatus} onToggle={onToggleAutopilot} />

      <StatsRow
        videosCount={videos.length}
        subscribers={channel ? channel.subscriber_count : 'NOT AVAILABLE'}
        totalViews={channel ? channel.view_count : 'NOT AVAILABLE'}
        channelTitle={channel ? channel.title : undefined}
      />

      <div className="two-col-grid">
        <ActivityFeed events={activityEvents} />

        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div className="stat-header">
            <span style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)' }}>
              Quick Action
            </span>
            <span>⚡</span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', lineHeight: 1.5 }}>
            Manually trigger the full autopilot pipeline now. Researches, scripts, synthesizes voice, transcribes, renders 1080x1920 MP4 via FFmpeg, and verifies QC gate (&gt;=90/100).
          </p>
          <button className="btn btn-primary" onClick={onGenerateClick} style={{ marginTop: 'auto' }}>
            + Create & Render Short Now
          </button>
        </div>
      </div>
    </div>
  );
};
