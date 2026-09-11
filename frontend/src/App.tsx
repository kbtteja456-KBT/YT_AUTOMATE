import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { CircuitStormCanvas } from './components/CircuitStormCanvas';
import { DashboardPage } from './pages/DashboardPage';
import { VideosPage } from './pages/VideosPage';
import { ProvidersPage } from './pages/ProvidersPage';
import { StylePage } from './pages/StylePage';
import { SettingsPage } from './pages/SettingsPage';
import { AdminPage } from './pages/AdminPage';
import { AuthPage } from './pages/AuthPage';
import { LandingPage } from './pages/LandingPage';
import { PrivacyPage } from './pages/PrivacyPage';
import { TermsPage } from './pages/TermsPage';
import { ApiKeyVaultModal } from './components/ApiKeyVaultModal';
import { CreateVideoModal } from './components/CreateVideoModal';
import {
  api,
  getToken,
  UserProfile,
  WorkspaceContext,
  AutopilotStatusResponse,
  ProvidersHealthResponse,
  ActivityEventItem,
  VideoItem,
  ChannelInfo
} from './services/api';

export const App: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [currentWorkspace, setCurrentWorkspace] = useState<WorkspaceContext | null>(null);
  const [isAuthChecking, setIsAuthChecking] = useState<boolean>(true);
  const [isVaultOpen, setIsVaultOpen] = useState<boolean>(false);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(false);

  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [autopilotStatus, setAutopilotStatus] = useState<AutopilotStatusResponse | null>(null);
  const [providersHealth, setProvidersHealth] = useState<ProvidersHealthResponse | null>(null);
  const [activityEvents, setActivityEvents] = useState<ActivityEventItem[]>([]);
  const [videos, setVideos] = useState<VideoItem[]>([]);
  const [channelInfo, setChannelInfo] = useState<ChannelInfo | null>(null);
  const [isGenerating] = useState<boolean>(false);
  const [publicView, setPublicView] = useState<'landing' | 'auth' | 'privacy' | 'terms'>(() => {
    if (typeof window !== 'undefined') {
      if (window.location.pathname === '/privacy') return 'privacy';
      if (window.location.pathname === '/terms') return 'terms';
    }
    return 'landing';
  });

  useEffect(() => {
    const handlePopState = () => {
      if (window.location.pathname === '/privacy') setPublicView('privacy');
      else if (window.location.pathname === '/terms') setPublicView('terms');
      else setPublicView('landing');
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const navigateTo = (view: 'landing' | 'auth' | 'privacy' | 'terms') => {
    setPublicView(view);
    const path = view === 'privacy' ? '/privacy' : view === 'terms' ? '/terms' : '/';
    window.history.pushState({}, '', path);
  };

  useEffect(() => {
    checkSession();
    if (typeof window !== 'undefined' && window.location.search.includes('youtube_connected=true')) {
      window.history.replaceState({}, '', window.location.pathname);
      loadAllData();
    }
  }, []);

  const checkSession = async () => {
    setIsAuthChecking(true);
    const token = getToken();
    if (!token) {
      setIsAuthChecking(false);
      return;
    }

    try {
      const me = await api.getMe();
      setCurrentUser(me.user);
      setCurrentWorkspace(me.workspace);
      await loadAllData();
    } catch (e) {
      console.warn('Session verification note:', e);
      api.logout();
    } finally {
      setIsAuthChecking(false);
    }
  };

  useEffect(() => {
    if (!currentUser) return;

    const interval = setInterval(() => {
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
  }, [currentUser]);

  const loadAllData = async () => {
    try {
      const [status, health, act, vids, chan, me] = await Promise.all([
        api.getAutopilotStatus().catch(() => null),
        api.getProvidersHealth().catch(() => null),
        api.getActivity().catch(() => []),
        api.getVideos().catch(() => []),
        api.getConnectedChannel().catch(() => null),
        api.getMe().catch(() => null),
      ]);
      if (status) setAutopilotStatus(status);
      if (health) setProvidersHealth(health);
      setActivityEvents(act);
      setVideos(vids);
      if (chan) setChannelInfo(chan);
      if (me) {
        setCurrentUser(me.user);
        setCurrentWorkspace(me.workspace);
      }
    } catch (e) {
      console.error('Data poll error:', e);
    }
  };

  const handleAuthenticated = (user: UserProfile, workspace: WorkspaceContext) => {
    setCurrentUser(user);
    setCurrentWorkspace(workspace);
    loadAllData();
  };

  const handleLogout = () => {
    api.logout();
    setCurrentUser(null);
    setCurrentWorkspace(null);
    setActiveTab('dashboard');
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

  const handleTriggerGenerate = () => {
    setIsCreateModalOpen(true);
  };

  const handleVideoQueued = (_jobId: string) => {
    loadAllData();
    setActiveTab('videos');
  };

  const handleVideoDeleted = (deletedId: string) => {
    setVideos((prev) => prev.filter((v) => v.id !== deletedId));
    loadAllData();
  };

  // Public legal compliance routes accessible at any time
  if (publicView === 'privacy') {
    return (
      <div className="app-container" style={{ position: 'relative', width: '100%', minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', overflowX: 'hidden', overflowY: 'auto' }}>
        <CircuitStormCanvas />
        <PrivacyPage
          onBack={() => navigateTo(currentUser ? 'landing' : 'landing')}
        />
      </div>
    );
  }

  if (publicView === 'terms') {
    return (
      <div className="app-container" style={{ position: 'relative', width: '100%', minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', overflowX: 'hidden', overflowY: 'auto' }}>
        <CircuitStormCanvas />
        <TermsPage
          onBack={() => navigateTo(currentUser ? 'landing' : 'landing')}
        />
      </div>
    );
  }

  // If unauthenticated: show LandingPage with 3D CircuitStorm background by default, or AuthPage if Sign In was clicked
  if (!isAuthChecking && !currentUser) {
    if (publicView === 'auth') {
      return (
        <div className="app-container" style={{ position: 'relative', width: '100%', minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', overflowX: 'hidden', overflowY: 'auto' }}>
          <CircuitStormCanvas />
          <AuthPage
            onAuthenticated={handleAuthenticated}
            onBack={() => navigateTo('landing')}
          />
        </div>
      );
    }

    return (
      <div className="app-container" style={{ position: 'relative', width: '100%', minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', overflowX: 'hidden', overflowY: 'auto' }}>
        <CircuitStormCanvas />
        <LandingPage
          onLoginClick={() => navigateTo('auth')}
          onPrivacyClick={() => navigateTo('privacy')}
          onTermsClick={() => navigateTo('terms')}
        />
      </div>
    );
  }

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
      case 'admin':
        return <AdminPage />;
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
      case 'admin': return 'Platform Admin & Costs';
      default: return 'Autopilot Dashboard';
    }
  };

  const connectedChannel = channelInfo?.is_connected ? channelInfo.channel : null;
  const isLegacyOwner = currentWorkspace?.is_legacy_default ?? currentUser?.is_owner ?? false;

  return (
    <div className="app-container">
      <CircuitStormCanvas />
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isOwner={currentUser?.is_owner}
        onOpenVault={() => setIsVaultOpen(true)}
      />
      <div className="main-content">
        <Header
          title={getPageTitle()}
          zeroCostMode={autopilotStatus?.zero_cost_mode ?? true}
          channelTitle={connectedChannel?.title || currentWorkspace?.name}
          channelAvatar={connectedChannel?.thumbnail_url}
          isGenerating={isGenerating}
          onGenerateClick={handleTriggerGenerate}
          onOpenVault={() => setIsVaultOpen(true)}
          trialVideosUsed={currentWorkspace?.trial_quota?.videos_generated}
          trialMaxVideos={currentWorkspace?.trial_quota?.max_videos}
          isLegacyOwner={isLegacyOwner}
          onLogout={handleLogout}
        />
        {renderActivePage()}
      </div>

      <ApiKeyVaultModal
        isOpen={isVaultOpen}
        onClose={() => setIsVaultOpen(false)}
        onKeysUpdated={loadAllData}
      />

      <CreateVideoModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onVideoQueued={handleVideoQueued}
        defaultNiche={currentWorkspace?.niche}
        hasConnectedChannel={Boolean(channelInfo?.is_connected)}
      />
    </div>
  );
};

export default App;
