/**
 * API service communicating with FastAPI backend.
 */

const ENV_BACKEND_URL = ((import.meta as any).env?.VITE_API_URL || '').replace(/\/$/, '');
const isLocal = typeof window !== 'undefined' && (
  window.location.hostname === 'localhost' ||
  window.location.hostname === '127.0.0.1' ||
  window.location.hostname.endsWith('.local')
);

// Fallback to the live production Render backend when hosted on Vercel/cloud if VITE_API_URL is unset
export const BACKEND_URL = ENV_BACKEND_URL || (isLocal ? '' : 'https://yt1-w757.onrender.com');
const API_BASE = BACKEND_URL ? `${BACKEND_URL}/api` : '/api';

export const resolveMediaUrl = (url: string | null | undefined): string => {
  if (!url) return '';
  if (url.startsWith('http://') || url.startsWith('https://')) return url;
  if (BACKEND_URL && url.startsWith('/')) return `${BACKEND_URL}${url}`;
  return url;
};

// Resilient Storage Manager with Memory Fallback (prevents DOMException: Access is denied)
const memoryStore: Record<string, string> = {};

const safeGetItem = (key: string): string | null => {
  try {
    if (typeof window !== 'undefined' && 'localStorage' in window) {
      const val = window.localStorage.getItem(key);
      if (val) return val;
    }
  } catch (e) {
    // Access denied by browser security / incognito / iframe
  }
  return memoryStore[key] || null;
};

const safeSetItem = (key: string, value: string): void => {
  memoryStore[key] = value;
  try {
    if (typeof window !== 'undefined' && 'localStorage' in window) {
      window.localStorage.setItem(key, value);
    }
  } catch (e) {
    // Access denied
  }
};

const safeRemoveItem = (key: string): void => {
  delete memoryStore[key];
  try {
    if (typeof window !== 'undefined' && 'localStorage' in window) {
      window.localStorage.removeItem(key);
    }
  } catch (e) {
    // Access denied
  }
};

// Token Storage
export const getToken = (): string | null => {
  return safeGetItem('yt_auth_token');
};

export const setToken = (token: string): void => {
  safeSetItem('yt_auth_token', token);
};

export const clearToken = (): void => {
  safeRemoveItem('yt_auth_token');
};

export const authFetch = async (url: string, options: RequestInit = {}): Promise<Response> => {
  const token = getToken();
  const headers = new Headers(options.headers || {});
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  return fetch(url, { ...options, headers });
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
  stage?: string;
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
  status?: string;
  views?: number;
  likes?: number;
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

export interface UserProfile {
  id: string;
  email: string;
  full_name?: string;
  is_owner: boolean;
}

export interface WorkspaceContext {
  id: string;
  name: string;
  slug: string;
  is_legacy_default: boolean;
  autopilot_enabled: boolean;
  niche: string;
  schedule: {
    slot_1_time: string;
    slot_2_time: string;
    timezone: string;
  };
  trial_quota?: {
    max_videos: number;
    videos_generated: number;
    max_ai_tokens: number;
    ai_tokens_used: number;
    max_tts_seconds: number;
    tts_seconds_used: number;
    is_exhausted: boolean;
  };
  connected_channel?: {
    channel_id: string;
    title: string;
    thumbnail_url?: string;
    subscriber_count?: number;
    custom_url?: string;
  };
}

export interface MeResponse {
  user: UserProfile;
  workspace: WorkspaceContext;
}

export interface VaultKeyInfo {
  key_mask: string;
  is_valid: boolean;
  last_tested_at?: string;
  provider: string;
}

export interface AcquisitionGuide {
  name: string;
  cost: string;
  step_by_step: string[];
  signup_url: string;
}

export interface VaultResponse {
  workspace_id: string;
  configured_keys: Record<string, VaultKeyInfo>;
  acquisition_guides: Record<string, AcquisitionGuide>;
}

export const api = {
  // Authentication & Session
  async register(email: string, password: string, full_name?: string): Promise<{ access_token: string; user: UserProfile; workspace: WorkspaceContext }> {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, full_name })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Registration failed' }));
      throw new Error(err.detail || 'Registration failed');
    }
    const data = await res.json();
    setToken(data.access_token);
    return data;
  },

  async login(email: string, password: string): Promise<{ access_token: string; user: UserProfile; workspace: WorkspaceContext }> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Invalid credentials' }));
      throw new Error(err.detail || 'Invalid email or password');
    }
    const data = await res.json();
    setToken(data.access_token);
    return data;
  },

  async getMe(): Promise<MeResponse> {
    const res = await authFetch(`${API_BASE}/auth/me`);
    if (!res.ok) throw new Error('Session expired');
    return res.json();
  },

  logout(): void {
    clearToken();
  },

  // BYOK Vault
  async getVaultKeys(): Promise<VaultResponse> {
    const res = await authFetch(`${API_BASE}/vault/keys`);
    if (!res.ok) throw new Error('Failed to load key vault');
    return res.json();
  },

  async saveVaultKey(provider: string, apiKey: string): Promise<{ status: string; key_mask: string; message: string }> {
    const res = await authFetch(`${API_BASE}/vault/keys`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider, api_key: apiKey })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Key verification failed' }));
      throw new Error(err.detail || 'Failed to save key');
    }
    return res.json();
  },

  async deleteVaultKey(provider: string): Promise<{ status: string }> {
    const res = await authFetch(`${API_BASE}/vault/keys/${provider}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete key');
    return res.json();
  },

  // Admin Cost & Usage
  async getAdminOverview(): Promise<any> {
    const res = await authFetch(`${API_BASE}/admin/overview`);
    if (!res.ok) throw new Error('Failed to fetch admin overview');
    return res.json();
  },

  async getAdminUsage(limit: number = 50): Promise<any> {
    const res = await authFetch(`${API_BASE}/admin/usage?limit=${limit}`);
    if (!res.ok) throw new Error('Failed to fetch usage ledger');
    return res.json();
  },

  async toggleWorkspace(workspaceId: string, autopilotEnabled: boolean): Promise<any> {
    const res = await authFetch(`${API_BASE}/admin/toggle-workspace`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ workspace_id: workspaceId, autopilot_enabled: autopilotEnabled })
    });
    if (!res.ok) throw new Error('Failed to toggle workspace status');
    return res.json();
  },

  // Pipeline & Dashboard Endpoints
  async getHealth(): Promise<HealthResponse> {
    const res = await authFetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Backend health check failed');
    return res.json();
  },

  async getProvidersHealth(): Promise<ProvidersHealthResponse> {
    const res = await authFetch(`${API_BASE}/providers/health`);
    if (!res.ok) throw new Error('Provider health check failed');
    return res.json();
  },

  async getAutopilotStatus(): Promise<AutopilotStatusResponse> {
    const res = await authFetch(`${API_BASE}/autopilot/status`);
    if (!res.ok) throw new Error('Failed to fetch autopilot status');
    return res.json();
  },

  async startAutopilot(): Promise<{ is_enabled: boolean; message: string }> {
    const res = await authFetch(`${API_BASE}/autopilot/start`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to start autopilot');
    return res.json();
  },

  async stopAutopilot(): Promise<{ is_enabled: boolean; message: string }> {
    const res = await authFetch(`${API_BASE}/autopilot/stop`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to stop autopilot');
    return res.json();
  },

  async getActivity(): Promise<ActivityEventItem[]> {
    const res = await authFetch(`${API_BASE}/activity`);
    if (!res.ok) throw new Error('Failed to fetch activity');
    return res.json();
  },

  async getVideos(): Promise<VideoItem[]> {
    const res = await authFetch(`${API_BASE}/videos`);
    if (!res.ok) throw new Error('Failed to fetch videos');
    return res.json();
  },

  async deleteVideo(videoId: string): Promise<{ status: string; video_id: string; title?: string }> {
    const res = await authFetch(`${API_BASE}/videos/${videoId}`, {
      method: 'DELETE'
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to delete video' }));
      throw new Error(err.detail || 'Failed to delete video');
    }
    return res.json();
  },

  async triggerGenerate(
    params?: string | {
      topic?: string;
      prompt?: string;
      content_format?: string;
      duration?: number;
      auto_publish?: boolean;
    },
    duration: number = 45
  ): Promise<{ job_id: string; message: string }> {
    let payload: any = { slot_index: 1 };
    if (typeof params === 'string') {
      payload.topic = params;
      payload.target_duration_sec = duration;
      payload.auto_publish = false;
    } else if (params && typeof params === 'object') {
      payload.topic = params.topic;
      payload.prompt = params.prompt;
      payload.content_format = params.content_format || 'auto';
      payload.target_duration_sec = params.duration || 45;
      payload.auto_publish = params.auto_publish || false;
    } else {
      payload.target_duration_sec = duration;
      payload.auto_publish = false;
    }

    const res = await authFetch(`${API_BASE}/videos/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to queue video generation' }));
      throw new Error(err.detail || 'Failed to queue video generation');
    }
    return res.json();
  },

  async updateVideo(
    videoId: string,
    data: { title?: string; description?: string; tags?: string[] }
  ): Promise<VideoItem> {
    const res = await authFetch(`${API_BASE}/videos/${videoId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to update video metadata' }));
      throw new Error(err.detail || 'Failed to update video metadata');
    }
    return res.json();
  },

  async getSettings(): Promise<any> {
    const res = await authFetch(`${API_BASE}/settings`);
    if (!res.ok) throw new Error('Failed to fetch settings');
    return res.json();
  },

  async updateSettings(settings: any): Promise<any> {
    const res = await authFetch(`${API_BASE}/settings`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings)
    });
    if (!res.ok) throw new Error('Failed to update settings');
    return res.json();
  },

  async getStyleProfile(): Promise<any> {
    const res = await authFetch(`${API_BASE}/style/profile`);
    if (!res.ok) throw new Error('Failed to fetch style profile');
    return res.json();
  },

  async uploadReferenceVideo(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await authFetch(`${API_BASE}/style/analyze`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) throw new Error('Failed to upload reference video');
    return res.json();
  },

  async getConnectedChannel(): Promise<ChannelInfo> {
    const res = await authFetch(`${API_BASE}/auth/youtube/channel`);
    if (!res.ok) throw new Error('Failed to fetch channel status');
    return res.json();
  },

  async syncChannel(): Promise<{ status: string; channel: any; message: string }> {
    const res = await authFetch(`${API_BASE}/auth/youtube/sync`, { method: 'POST' });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to sync with YouTube');
    }
    return res.json();
  },

  async getConnectUrl(): Promise<string> {
    const token = getToken();
    const endpoint = token ? `${API_BASE}/tenant/youtube/connect` : `${API_BASE}/auth/youtube/connect`;
    const res = await authFetch(endpoint, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to get auth url');
    const data = await res.json();
    return data.auth_url;
  },

  async publishVideo(videoId: string): Promise<{ status: string; youtube_video_id?: string; youtube_url?: string; message: string }> {
    const res = await authFetch(`${API_BASE}/videos/${videoId}/publish`, { method: 'POST' });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to publish video to YouTube');
    }
    return res.json();
  }
};
