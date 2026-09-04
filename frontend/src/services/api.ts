/**
 * API service communicating with FastAPI backend.
 */

export const BACKEND_URL = ((import.meta as any).env?.VITE_API_URL || '').replace(/\/$/, '');
const API_BASE = BACKEND_URL ? `${BACKEND_URL}/api` : '/api';

export const resolveMediaUrl = (url: string | null | undefined): string => {
  if (!url) return '';
  if (url.startsWith('http://') || url.startsWith('https://')) return url;
  if (BACKEND_URL && url.startsWith('/')) return `${BACKEND_URL}${url}`;
  return url;
};

export interface HealthResponse {
  status: string;
  app: string;
  version: string;
  zero_cost_mode: boolean;
  timezone: string;
  daily_video_limit: number;
  system_resources: {
    ram_available_mb: number;
    ram_total_mb: number;
    disk_free_gb: number;
    disk_total_gb: number;
    cpu_percent: number;
    is_safe_for_rendering: boolean;
  };
}

export interface ProviderHealthItem {
  provider: string;
  status: 'CONNECTED' | 'DEGRADED' | 'OFFLINE' | 'BLOCKED_ZERO_COST' | 'NOT_CONFIGURED';
  is_zero_cost: boolean;
  message: string;
}

export interface ProvidersHealthResponse {
  timestamp: number;
  zero_cost_mode: boolean;
  subsystems: Record<string, ProviderHealthItem>;
}

export interface AutopilotStatusResponse {
  is_enabled: boolean;
  daily_limit: number;
  slot_1_time: string;
  slot_2_time: string;
  timezone: string;
  zero_cost_mode: boolean;
  status_today: {
    slot_1: string;
    slot_2: string;
  };
}

export interface ActivityEventItem {
  id?: string;
  event_type: string;
  level: string;
  agent_name?: string;
  job_id?: string;
  message: string;
  timestamp: string;
}

export interface VideoItem {
  id: string;
  title: string;
  description: string;
  tags?: string[];
  thumbnail_path?: string;
  thumbnail_url?: string;
  file_path?: string;
  video_url?: string;
  duration_seconds: number;
  quality_score: number;
  youtube_video_id?: string;
  youtube_url?: string;
  created_at: string;
}

export interface ChannelInfo {
  is_connected: boolean;
  channel?: {
    channel_id: string;
    title: string;
    description?: string;
    custom_url?: string;
    subscriber_count: number;
    view_count: number;
    video_count: number;
    thumbnail_url?: string;
    connected_at?: string;
  } | null;
}

export const api = {
  async getHealth(): Promise<HealthResponse> {
    const res = await fetch('/health');
    if (!res.ok) throw new Error('Health check failed');
    return res.json();
  },

  async getProvidersHealth(): Promise<ProvidersHealthResponse> {
    const res = await fetch('/providers/health');
    if (!res.ok) throw new Error('Provider health check failed');
    return res.json();
  },

  async getAutopilotStatus(): Promise<AutopilotStatusResponse> {
    const res = await fetch(`${API_BASE}/autopilot/status`);
    if (!res.ok) throw new Error('Failed to fetch autopilot status');
    return res.json();
  },

  async startAutopilot(): Promise<{ is_enabled: boolean; message: string }> {
    const res = await fetch(`${API_BASE}/autopilot/start`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to start autopilot');
    return res.json();
  },

  async stopAutopilot(): Promise<{ is_enabled: boolean; message: string }> {
    const res = await fetch(`${API_BASE}/autopilot/stop`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to stop autopilot');
    return res.json();
  },

  async getActivity(): Promise<ActivityEventItem[]> {
    const res = await fetch(`${API_BASE}/activity`);
    if (!res.ok) throw new Error('Failed to fetch activity');
    return res.json();
  },

  async getVideos(): Promise<VideoItem[]> {
    const res = await fetch(`${API_BASE}/videos`);
    if (!res.ok) throw new Error('Failed to fetch videos');
    return res.json();
  },

  async triggerGenerate(topic?: string, duration: number = 45): Promise<{ job_id: string; message: string }> {
    const res = await fetch(`${API_BASE}/videos/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic, target_duration_sec: duration, slot_index: 1 })
    });
    if (!res.ok) throw new Error('Failed to queue video generation');
    return res.json();
  },

  async getSettings(): Promise<any> {
    const res = await fetch(`${API_BASE}/settings`);
    if (!res.ok) throw new Error('Failed to fetch settings');
    return res.json();
  },

  async updateSettings(settings: any): Promise<any> {
    const res = await fetch(`${API_BASE}/settings`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings)
    });
    if (!res.ok) throw new Error('Failed to update settings');
    return res.json();
  },

  async getStyleProfile(): Promise<any> {
    const res = await fetch(`${API_BASE}/style/profile`);
    if (!res.ok) throw new Error('Failed to fetch style profile');
    return res.json();
  },

  async uploadReferenceVideo(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/style/analyze`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) throw new Error('Failed to upload reference video');
    return res.json();
  },

  async getConnectedChannel(): Promise<ChannelInfo> {
    const res = await fetch(`${API_BASE}/auth/youtube/channel`);
    if (!res.ok) throw new Error('Failed to fetch channel status');
    return res.json();
  },

  async syncChannel(): Promise<{ status: string; channel: any; message: string }> {
    const res = await fetch(`${API_BASE}/auth/youtube/sync`, { method: 'POST' });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to sync with YouTube');
    }
    return res.json();
  },

  async getConnectUrl(): Promise<string> {
    const res = await fetch(`${API_BASE}/auth/youtube/connect`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to get auth url');
    const data = await res.json();
    return data.auth_url;
  }
};
