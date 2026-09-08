import React from 'react';

interface IconProps {
  className?: string;
  size?: number;
  color?: string;
  style?: React.CSSProperties;
}

export const PlayTileIcon: React.FC<{ size?: number }> = ({ size = 36 }) => (
  <svg width={size} height={size} viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="logoGrad" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
        <stop stopColor="#fbbf24" />
        <stop offset="0.6" stopColor="#f59e0b" />
        <stop offset="1" stopColor="#d97706" />
      </linearGradient>
      <filter id="logoShadow" x="-20%" y="-20%" width="140%" height="140%">
        <feDropShadow dx="0" dy="4" stdDeviation="4" floodColor="#d97706" floodOpacity="0.45" />
      </filter>
    </defs>
    <rect x="2" y="2" width="36" height="36" rx="11" fill="url(#logoGrad)" filter="url(#logoShadow)" stroke="rgba(255,255,255,0.4)" strokeWidth="1" />
    <path d="M16.5 13.5L27 20L16.5 26.5V13.5Z" fill="white" />
  </svg>
);

export const YouTubeRedTileIcon: React.FC<{ size?: number }> = ({ size = 42 }) => (
  <svg width={size} height={size} viewBox="0 0 44 44" fill="none" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="ytRedGrad" x1="0" y1="0" x2="44" y2="44" gradientUnits="userSpaceOnUse">
        <stop stopColor="#ff3344" />
        <stop offset="1" stopColor="#cc0000" />
      </linearGradient>
      <filter id="ytRedShadow" x="-20%" y="-20%" width="140%" height="140%">
        <feDropShadow dx="0" dy="5" stdDeviation="6" floodColor="#ff0000" floodOpacity="0.4" />
      </filter>
    </defs>
    <rect x="2" y="2" width="40" height="40" rx="12" fill="url(#ytRedGrad)" filter="url(#ytRedShadow)" stroke="rgba(255,255,255,0.3)" strokeWidth="1" />
    <path d="M18 15L29 22L18 29V15Z" fill="white" />
  </svg>
);

export const CalendarAmberTileIcon: React.FC<{ size?: number }> = ({ size = 48 }) => (
  <svg width={size} height={size} viewBox="0 0 52 52" fill="none" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="calGrad" x1="0" y1="0" x2="52" y2="52" gradientUnits="userSpaceOnUse">
        <stop stopColor="#fbbf24" />
        <stop offset="0.6" stopColor="#f59e0b" />
        <stop offset="1" stopColor="#d97706" />
      </linearGradient>
      <filter id="calShadow" x="-20%" y="-20%" width="140%" height="140%">
        <feDropShadow dx="0" dy="6" stdDeviation="6" floodColor="#d97706" floodOpacity="0.4" />
      </filter>
    </defs>
    <rect x="3" y="3" width="46" height="46" rx="14" fill="url(#calGrad)" filter="url(#calShadow)" stroke="rgba(255,255,255,0.35)" strokeWidth="1.2" />
    <rect x="12" y="10" width="28" height="5" rx="2" fill="rgba(255,255,255,0.8)" />
    <circle cx="18" cy="9" r="2" fill="#78350f" />
    <circle cx="34" cy="9" r="2" fill="#78350f" />
    <path d="M22 23L33 29.5L22 36V23Z" fill="white" />
  </svg>
);

export const CalendarBlueTileIcon = CalendarAmberTileIcon;

export const DashboardIcon: React.FC<IconProps> = ({ size = 18, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
    <polyline points="9 22 9 12 15 12 15 22" />
  </svg>
);

export const VideosIcon: React.FC<IconProps> = ({ size = 18, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect width="20" height="20" x="2" y="2" rx="4" />
    <path d="M2 8h20" />
    <path d="m6 2 3 6" />
    <path d="m15 2 3 6" />
    <path d="m11 12 5 3-5 3v-6Z" fill={color} />
  </svg>
);

export const HealthIcon: React.FC<IconProps> = ({ size = 18, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
  </svg>
);

export const StyleIcon: React.FC<IconProps> = ({ size = 18, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z" />
    <path d="m15 5 4 4" />
  </svg>
);

export const SettingsIcon: React.FC<IconProps> = ({ size = 18, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
  </svg>
);

export const CheckCircleIcon: React.FC<IconProps> = ({ size = 14, color = '#10b981' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12" />
  </svg>
);

export const ClockIcon: React.FC<IconProps> = ({ size = 14, color = '#f59e0b' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <polyline points="12 6 12 12 16 14" />
  </svg>
);

export const SyncIcon: React.FC<IconProps> = ({ size = 14, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67" />
  </svg>
);

export const ChevronDownIcon: React.FC<IconProps> = ({ size = 14, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="m6 9 6 6 6-6" />
  </svg>
);

export const PauseIcon: React.FC<IconProps> = ({ size = 16, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill={color}>
    <rect x="6" y="4" width="4" height="16" rx="1.5" />
    <rect x="14" y="4" width="4" height="16" rx="1.5" />
  </svg>
);

export const PlayIcon: React.FC<IconProps> = ({ size = 16, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill={color}>
    <polygon points="5 3 19 12 5 21 5 3" />
  </svg>
);

export const SparklineAmber: React.FC<{ width?: number; height?: number }> = ({ width = 110, height = 36 }) => (
  <svg width={width} height={height} viewBox="0 0 120 40" fill="none" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="amberSparkGrad" x1="0" y1="0" x2="0" y2="40" gradientUnits="userSpaceOnUse">
        <stop stopColor="#f59e0b" stopOpacity="0.4" />
        <stop offset="1" stopColor="#f59e0b" stopOpacity="0" />
      </linearGradient>
    </defs>
    <path
      d="M0 32 C 25 32, 35 30, 50 25 C 65 20, 75 14, 90 20 C 105 26, 110 8, 120 4"
      stroke="#f59e0b"
      strokeWidth="2.5"
      strokeLinecap="round"
    />
    <path
      d="M0 32 C 25 32, 35 30, 50 25 C 65 20, 75 14, 90 20 C 105 26, 110 8, 120 4 V 40 H 0 Z"
      fill="url(#amberSparkGrad)"
    />
  </svg>
);

export const SparklineBlue = SparklineAmber;

export const SparklineGreen: React.FC<{ width?: number; height?: number }> = ({ width = 110, height = 36 }) => (
  <svg width={width} height={height} viewBox="0 0 120 40" fill="none" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="greenSparkGrad" x1="0" y1="0" x2="0" y2="40" gradientUnits="userSpaceOnUse">
        <stop stopColor="#10b981" stopOpacity="0.4" />
        <stop offset="1" stopColor="#10b981" stopOpacity="0" />
      </linearGradient>
    </defs>
    <path
      d="M0 34 C 20 34, 30 26, 45 28 C 60 30, 70 18, 85 22 C 100 26, 110 6, 120 2"
      stroke="#10b981"
      strokeWidth="2.5"
      strokeLinecap="round"
    />
    <path
      d="M0 34 C 20 34, 30 26, 45 28 C 60 30, 70 18, 85 22 C 100 26, 110 6, 120 2 V 40 H 0 Z"
      fill="url(#greenSparkGrad)"
    />
  </svg>
);

export const TrashIcon: React.FC<IconProps> = ({ size = 16, color = 'currentColor', style }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    style={style}
  >
    <path d="M3 6h18" />
    <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
    <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
    <line x1="10" x2="10" y1="11" y2="17" />
    <line x1="14" x2="14" y1="11" y2="17" />
  </svg>
);

export const KeyIcon: React.FC<IconProps> = ({ size = 18, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="7.5" cy="15.5" r="5.5" />
    <path d="m21 2-9.6 9.6" />
    <path d="m15.5 7.5 3 3L22 7l-3-3" />
  </svg>
);

export const ShieldIcon: React.FC<IconProps> = ({ size = 18, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
);

export const SparklesIcon: React.FC<IconProps> = ({ size = 18, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
  </svg>
);

export const ExternalLinkIcon: React.FC<IconProps> = ({ size = 14, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
    <polyline points="15 3 21 3 21 9" />
    <line x1="10" y1="14" x2="21" y2="3" />
  </svg>
);

export const RefreshIcon: React.FC<IconProps> = ({ size = 16, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
    <path d="M3 3v5h5" />
    <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
    <path d="M16 21h5v-5" />
  </svg>
);
