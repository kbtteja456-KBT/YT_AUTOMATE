import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { CircuitStormCanvas } from './components/CircuitStormCanvas';
import { DashboardPage } from './pages/DashboardPage';
import { VideosPage } from './pages/VideosPage';
import { ProvidersPage } from './pages/ProvidersPage';
import { StylePage } from './pages/StylePage';
import { SettingsPage } from './pages/SettingsPage';
import {
  api,
  AutopilotStatusResponse,
  ProvidersHealthResponse,
  ActivityEventItem,
  VideoItem,
  ChannelInfo
} from './services/api';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [autopilotStatus, setAutopilotStatus] = useState<AutopilotStatusResponse | null>(null);
  const [providersHealth, setProvidersHealth] = useState<ProvidersHealthResponse | null>(null);
  const [activityEvents, setActivityEvents] = useState<ActivityEventItem[]>([]);
  const [videos, setVideos] = useState<VideoItem[]>([]);
  const [channelInfo, setChannelInfo] = useState<ChannelInfo | null>(null);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);

  useEffect(() => {
    loadAllData();

    const interval = setInterval(() => {
      // Don't poll when mobile screen is turned off or tab is in background
      if (!document.hidden) {
        loadAllData();
      }
    }, 12000);

    const handleVisibilityChange = () => {
      if (!document.hidden) {
        loadAllData();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      clearInterval(interval);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  const loadAllData = async () => {
    try {
      const [status, health, act, vids, chan] = await Promise.all([
        api.getAutopilotStatus().catch(() => null),
        api.getProvidersHealth().catch(() => null),
        api.getActivity().catch(() => []),
        api.getVideos().catch(() => []),
        api.getConnectedChannel().catch(() => null)
      ]);
      if (status) setAutopilotStatus(status);
      if (health) setProvidersHealth(health);
      setActivityEvents(act);
      setVideos(vids);
      if (chan) setChannelInfo(chan);
    } catch (e) {
      console.error('Data poll error:', e);
    }
  };

  const handleToggleAutopilot = async () => {
    if (!autopilotStatus) return;
    try {
      if (autopilotStatus.is_enabled) {
        await api.stopAutopilot();
      } else {
        await api.startAutopilot();
      }
      await loadAllData();
    } catch (e) {
      console.error('Failed to toggle autopilot:', e);
    }
  };

  const handleTriggerGenerate = async () => {
    const topic = prompt('Enter Short topic (or leave empty for AI niche discovery):');
    if (topic === null) return;

    setIsGenerating(true);
    try {
      const res = await api.triggerGenerate(topic || undefined);
      alert(`Job Queued! ID: ${res.job_id}`);
      await loadAllData();
    } catch (e: any) {
      alert(`Error queuing job: ${e.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleVideoDeleted = (deletedId: string) => {
    setVideos((prev) => prev.filter((v) => v.id !== deletedId));
    loadAllData();
  };

  const renderActivePage = () => {
    switch (activeTab) {
      case 'videos':
        return (
          <VideosPage
            videos={videos}
            onGenerateClick={handleTriggerGenerate}
            onVideoDeleted={handleVideoDeleted}
          />
        );
      case 'providers':
        return <ProvidersPage healthData={providersHealth} onRefresh={loadAllData} />;
      case 'style':
        return <StylePage />;
      case 'settings':
        return <SettingsPage />;
      case 'dashboard':
      default:
        return (
          <DashboardPage
            autopilotStatus={autopilotStatus}
            activityEvents={activityEvents}
            videos={videos}
            channelInfo={channelInfo}
            onToggleAutopilot={handleToggleAutopilot}
            onGenerateClick={handleTriggerGenerate}
            onRefreshData={loadAllData}
          />
        );
    }
  };

  const getPageTitle = () => {
    switch (activeTab) {
      case 'videos': return 'Videos Library';
      case 'providers': return 'Provider Health';
      case 'style': return 'Style Analyzer';
      case 'settings': return 'Channel Settings';
      default: return 'Autopilot Dashboard';
    }
  };

  const connectedChannel = channelInfo?.is_connected ? channelInfo.channel : null;

  return (
    <div className="app-container">
      <CircuitStormCanvas />
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <div className="main-content">
        <Header
          title={getPageTitle()}
          zeroCostMode={autopilotStatus?.zero_cost_mode ?? true}
          channelTitle={connectedChannel?.title}
          channelAvatar={connectedChannel?.thumbnail_url}
          isGenerating={isGenerating}
          onGenerateClick={handleTriggerGenerate}
        />
        {renderActivePage()}
      </div>
    </div>
  );
};

export default App;
