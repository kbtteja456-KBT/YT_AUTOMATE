import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

export const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<any>(null);
  const [channelInfo, setChannelInfo] = useState<any>(null);
  const [saving, setSaving] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  useEffect(() => {
    loadSettings();
    loadChannelInfo();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await api.getSettings();
      setSettings(data);
    } catch (e) {
      console.error(e);
    }
  };

  const loadChannelInfo = async () => {
    try {
      const info = await api.getConnectedChannel();
      setChannelInfo(info);
    } catch (e) {
      console.error(e);
    }
  };

  const handleConnectChannel = async () => {
    setConnecting(true);
    try {
      const authUrl = await api.getConnectUrl();
      window.location.href = authUrl;
    } catch (err: any) {
      setStatusMsg(`Connection error: ${err.message || 'Could not initiate YouTube OAuth'}`);
      setConnecting(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setStatusMsg(null);
    try {
      await api.updateSettings(settings);
      setStatusMsg('Settings successfully updated!');
    } catch (err: any) {
      setStatusMsg(`Error: ${err.message || 'Failed to save'}`);
    } finally {
      setSaving(false);
    }
  };

  if (!settings) {
    return (
      <div className="page-body">
        <p>Loading settings...</p>
      </div>
    );
  }

  return (
    <div className="page-body">
      <div>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '22px' }}>System & Channel Settings</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '14px' }}>
          Configure autonomous publishing rules, Zero-Cost Mode, and AI models.
        </p>
      </div>

      <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '20px', maxWidth: '720px' }}>
        {/* Connected YouTube Channel Card */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '14px', border: channelInfo?.channel?.is_active === false ? '1px solid rgba(239,68,68,0.4)' : undefined }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: 700, margin: 0 }}>Connected YouTube Channel</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '13px', margin: '4px 0 0 0' }}>
                Authorization for automated Shorts publishing and channel analytics.
              </p>
            </div>
            {channelInfo?.channel ? (
              channelInfo.channel.is_active === false ? (
                <span style={{ fontSize: '12px', padding: '4px 10px', borderRadius: '6px', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#f87171', fontWeight: 600 }}>
                  ⚠️ Token Expired / Revoked
                </span>
              ) : (
                <span style={{ fontSize: '12px', padding: '4px 10px', borderRadius: '6px', background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.3)', color: '#10b981', fontWeight: 600 }}>
                  ✅ Channel Connected
                </span>
              )
            ) : (
              <span style={{ fontSize: '12px', padding: '4px 10px', borderRadius: '6px', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#f87171', fontWeight: 600 }}>
                ❌ No Channel Connected
              </span>
            )}
          </div>

          {channelInfo?.channel ? (
            <div style={{ background: 'rgba(0,0,0,0.25)', padding: '14px 16px', borderRadius: 'var(--radius-sm)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
              <div>
                <div style={{ fontWeight: 600, color: '#fff', fontSize: '15px' }}>{channelInfo.channel.title}</div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                  Channel ID: <code>{channelInfo.channel.channel_id}</code>
                </div>
                {channelInfo.channel.error_message && (
                  <div style={{ fontSize: '12px', color: '#f87171', marginTop: '4px' }}>
                    {channelInfo.channel.error_message}
                  </div>
                )}
              </div>
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleConnectChannel}
                disabled={connecting}
                style={{
                  background: 'linear-gradient(135deg, #ef4444, #dc2626)',
                  borderColor: '#ef4444',
                  color: '#fff',
                  fontSize: '13px',
                  padding: '8px 16px',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                {connecting ? 'Connecting...' : 'Reconnect YouTube Channel'}
              </button>
            </div>
          ) : (
            <div>
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleConnectChannel}
                disabled={connecting}
                style={{
                  background: 'linear-gradient(135deg, #ef4444, #dc2626)',
                  borderColor: '#ef4444',
                  color: '#fff',
                  fontSize: '13px',
                  padding: '8px 18px',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                {connecting ? 'Connecting...' : 'Connect YouTube Channel'}
              </button>
            </div>
          )}
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700 }}>Zero-Cost Hard Mode</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
            When enabled, all paid API calls (OpenRouter paid models, paid TTS, paid stock) are blocked outright.
          </p>
          <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={settings.zero_cost_mode}
              onChange={(e) => setSettings({ ...settings, zero_cost_mode: e.target.checked })}
              style={{ width: '18px', height: '18px' }}
            />
            <span style={{ fontWeight: 600, color: settings.zero_cost_mode ? 'var(--accent-mint)' : 'var(--text-secondary)' }}>
              Enable Zero-Cost Mode (₹0 Guarantee)
            </span>
          </label>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700 }}>Publishing Schedule & Timezone</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div>
              <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                Slot 1 (Morning)
              </label>
              <input
                type="text"
                value={settings.schedule?.slot1_time || '07:00'}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    schedule: { ...settings.schedule, slot1_time: e.target.value }
                  })
                }
                style={{ width: '100%', padding: '8px 12px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', color: '#fff' }}
              />
            </div>
            <div>
              <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                Slot 2 (Evening)
              </label>
              <input
                type="text"
                value={settings.schedule?.slot2_time || '18:00'}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    schedule: { ...settings.schedule, slot2_time: e.target.value }
                  })
                }
                style={{ width: '100%', padding: '8px 12px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', color: '#fff' }}
              />
            </div>
          </div>
          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
              Timezone
            </label>
            <input
              type="text"
              value={settings.schedule?.timezone || 'Asia/Kolkata'}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  schedule: { ...settings.schedule, timezone: e.target.value }
                })
              }
              style={{ width: '100%', padding: '8px 12px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', color: '#fff' }}
            />
          </div>
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '4px' }}>Content, Concept & Duration Configuration</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '13px', margin: 0 }}>
              Specify your full content, custom topic instructions, video duration, and preferred visual format.
            </p>
          </div>

          <div>
            <label style={{ fontSize: '13px', fontWeight: 600, color: '#f8fafc', display: 'block', marginBottom: '6px' }}>
              Primary Channel Niche
            </label>
            <input
              type="text"
              value={settings.niche || ''}
              placeholder="e.g. Python Programming, AI & Tech News, Deep Science, Stoic Philosophy"
              onChange={(e) => setSettings({ ...settings, niche: e.target.value })}
              style={{ width: '100%', padding: '10px 12px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', color: '#fff', fontSize: '14px' }}
            />
          </div>

          <div>
            <label style={{ fontSize: '13px', fontWeight: 600, color: '#f8fafc', display: 'block', marginBottom: '6px' }}>
              Full Content, Custom Topic & Script Guidelines
            </label>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '8px' }}>
              Enter full content, article summary, notes, or detailed instructions. The system will analyze this and generate videos strictly aligned with your text.
            </p>
            <textarea
              rows={4}
              value={settings.custom_content_prompt || ''}
              placeholder="e.g. Explain how autonomous AI coding agents work in 2026, including their reasoning loops, sandbox execution, and why developers use them. Focus on practical insights and real-world tools..."
              onChange={(e) => setSettings({ ...settings, custom_content_prompt: e.target.value })}
              style={{
                width: '100%',
                boxSizing: 'border-box',
                padding: '12px',
                background: 'rgba(0,0,0,0.3)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                color: '#fff',
                fontSize: '13.5px',
                lineHeight: 1.5,
                resize: 'vertical',
                fontFamily: 'inherit'
              }}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div>
              <label style={{ fontSize: '13px', fontWeight: 600, color: '#f8fafc', display: 'block', marginBottom: '6px' }}>
                Video Duration
              </label>
              <div style={{ display: 'flex', gap: '8px' }}>
                {[30, 45, 60].map((sec) => (
                  <button
                    type="button"
                    key={sec}
                    onClick={() => setSettings({ ...settings, default_duration_sec: sec })}
                    style={{
                      flex: 1,
                      padding: '8px 0',
                      borderRadius: '8px',
                      background: (settings.default_duration_sec || 45) === sec ? '#2563eb' : 'rgba(0,0,0,0.3)',
                      border: `1px solid ${(settings.default_duration_sec || 45) === sec ? '#3b82f6' : 'var(--border-subtle)'}`,
                      color: '#ffffff',
                      fontSize: '13px',
                      fontWeight: 600,
                      cursor: 'pointer'
                    }}
                  >
                    {sec}s
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label style={{ fontSize: '13px', fontWeight: 600, color: '#f8fafc', display: 'block', marginBottom: '6px' }}>
                Preferred Visual Format
              </label>
              <select
                value={settings.preferred_format || 'auto'}
                onChange={(e) => setSettings({ ...settings, preferred_format: e.target.value })}
                style={{
                  width: '100%',
                  padding: '9px 12px',
                  background: '#1e293b',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  color: '#fff',
                  fontSize: '13px',
                  cursor: 'pointer',
                  outline: 'none'
                }}
              >
                <option value="auto">✨ Auto-Detect from Content</option>
                <option value="documentary">📹 Documentary & Stories (Hybrid Videos & Photos)</option>
                <option value="quiz_card">💻 Code Quiz Challenge (Interactive Syntax Card)</option>
                <option value="quote_card">🏛️ Daily Motivation & Wisdom (Quote Card)</option>
                <option value="trivia_quiz">🧠 Trivia Riddle & Brain Teaser (Question Card)</option>
              </select>
            </div>
          </div>

          <div>
            <label style={{ fontSize: '13px', fontWeight: 600, color: '#f8fafc', display: 'block', marginBottom: '6px' }}>
              Target Audience Persona
            </label>
            <input
              type="text"
              value={settings.target_audience || ''}
              placeholder="e.g. Students, Junior Developers, Tech Enthusiasts"
              onChange={(e) => setSettings({ ...settings, target_audience: e.target.value })}
              style={{ width: '100%', padding: '10px 12px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', color: '#fff', fontSize: '14px' }}
            />
          </div>
        </div>

        <div>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? 'Saving...' : 'Save Configuration'}
          </button>
          {statusMsg && (
            <span style={{ marginLeft: '14px', fontSize: '13px', color: statusMsg.startsWith('Error') ? 'var(--accent-rose)' : 'var(--accent-mint)' }}>
              {statusMsg}
            </span>
          )}
        </div>
      </form>
    </div>
  );
};
