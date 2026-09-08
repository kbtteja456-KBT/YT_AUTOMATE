import React from 'react';
import {
  PlayTileIcon,
  DashboardIcon,
  VideosIcon,
  HealthIcon,
  StyleIcon,
  SettingsIcon,
  KeyIcon,
  ShieldIcon
} from './Icons';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  isOwner?: boolean;
  onOpenVault?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab, isOwner = false, onOpenVault }) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: <DashboardIcon size={18} /> },
    { id: 'videos', label: 'Videos Library', icon: <VideosIcon size={18} /> },
    { id: 'providers', label: 'Provider Health', icon: <HealthIcon size={18} /> },
    { id: 'style', label: 'Style Analyzer', icon: <StyleIcon size={18} /> },
    { id: 'settings', label: 'Settings', icon: <SettingsIcon size={18} /> },
  ];

  if (isOwner) {
    navItems.push({ id: 'admin', label: 'Admin & Costs', icon: <ShieldIcon size={18} /> });
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-icon-wrapper">
          <PlayTileIcon size={38} />
        </div>
        <div className="brand-text">
          <h1>Auto YouTube Video Bot</h1>
          <span className="brand-badge-zero-cost">Multi-Tenant AI</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              className={`nav-item ${isActive ? 'active' : ''}`}
              onClick={() => setActiveTab(item.id)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span>{item.label}</span>
            </button>
          );
        })}

        {onOpenVault && (
          <button
            className="nav-item"
            onClick={onOpenVault}
            style={{ marginTop: '8px', color: '#f59e0b' }}
          >
            <span className="nav-icon"><KeyIcon size={18} /></span>
            <span>API Key Vault</span>
          </button>
        )}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-art-container">
          <img
            src="/sidebar_glow.jpg"
            alt="3D Abstract Tech"
            className="sidebar-art-bg"
            onError={(e) => {
              // Graceful fallback if image is not loaded
              (e.target as HTMLElement).style.display = 'none';
            }}
          />
        </div>
        <div className="sidebar-motto" style={{ marginBottom: '8px' }}>
          Automate • Create • Grow 🚀
        </div>
        <div style={{ display: 'flex', gap: '8px', justifyContent: 'center', fontSize: '11px' }}>
          <a href="/privacy" style={{ color: '#8b949e', textDecoration: 'none' }}>Privacy</a>
          <span style={{ color: '#30363d' }}>•</span>
          <a href="/terms" style={{ color: '#8b949e', textDecoration: 'none' }}>Terms</a>
        </div>
      </div>
    </aside>
  );
};
