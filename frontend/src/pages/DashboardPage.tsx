import React from 'react';
import { AutopilotHero } from '../components/AutopilotHero';
import { StatsRow } from '../components/StatsRow';
import { ActivityFeed } from '../components/ActivityFeed';
import {
  AutopilotStatusResponse,
  ActivityEventItem,
  VideoItem,
  ChannelInfo,
  api
} from '../services/api';
import { YouTubeRedTileIcon, CheckCircleIcon, SyncIcon, ChevronDownIcon, PlayIcon } from '../components/Icons';

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
  const channelName = channel?.title || 'Bhanu Teja';
  const channelHandle = channel?.custom_url || '@bhanuteja-8';
  const channelId = channel?.channel_id || 'UCBQkctpyUEzsCmEbeJ8RQ';

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
      {/* 1. YouTube Connection Banner Card */}
      <div className="card yt-connected-card">
        <div className="yt-card-left">
          <YouTubeRedTileIcon size={44} />
          <div>
            <div className="yt-card-title-row">
              <span className="yt-channel-name">{channelName}</span>
              <span className="yt-channel-handle">{channelHandle}</span>
            </div>
            <div className="yt-channel-id">
              Channel ID: <code>{channelId}</code>
            </div>
          </div>
        </div>

        <div className="yt-card-right">
          <span className="yt-connected-badge">
            <CheckCircleIcon size={13} color="#10b981" />
            YouTube Connected
          </span>

          <button
            className="btn btn-secondary yt-sync-btn"
            onClick={handleSync}
            disabled={isSyncing}
          >
            <SyncIcon size={13} />
            <span>{isSyncing ? 'Syncing...' : 'Sync Stats'}</span>
            <ChevronDownIcon size={11} color="#94a3b8" />
          </button>
        </div>
      </div>

      {syncNotice && (
        <div style={{
          fontSize: '12.5px',
          padding: '8px 14px',
          borderRadius: '10px',
          background: syncNotice.includes('Authorization') ? 'rgba(59, 130, 246, 0.12)' : 'rgba(16, 185, 129, 0.12)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          color: '#93c5fd'
        }}>
          ℹ️ {syncNotice}
        </div>
      )}

      {/* 2. Autonomous Daily Publishing Hero Card */}
      <AutopilotHero status={autopilotStatus} onToggle={onToggleAutopilot} />

      {/* 3. Metric Cards Row */}
      <StatsRow
        videosCount={videos.length}
        subscribers={channel?.subscriber_count}
        totalViews={channel?.view_count}
        channelTitle={channel?.title}
      />

      {/* 4. Live Pipeline Activity & Quick Action Row */}
      <div className="bottom-dashboard-grid">
        <ActivityFeed events={activityEvents} />

        <div className="card quick-action-card">
          <div>
            <div className="quick-action-header">
              <div className="quick-action-tile">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="#ffffff">
                  <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
                </svg>
              </div>
              <h3 className="quick-action-title">Quick Action</h3>
            </div>
            <p className="quick-action-desc" style={{ marginTop: '12px' }}>
              Manually trigger the full autopilot pipeline now. Researches, scripts, synthesizes voice, transcribes, renders 1080x1920 MP4 via FFmpeg, and verifies QC gate (&gt;=90/100).
            </p>
          </div>

          <button
            className="btn btn-primary quick-action-btn"
            onClick={onGenerateClick}
          >
            <PlayIcon size={16} />
            <span>+ Create &amp; Render Short Now</span>
          </button>
        </div>
      </div>
    </div>
  );
};
