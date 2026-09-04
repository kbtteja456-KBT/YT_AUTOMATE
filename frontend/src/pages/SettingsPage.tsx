import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

export const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<any>(null);
  const [saving, setSaving] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await api.getSettings();
      setSettings(data);
    } catch (e) {
      console.error(e);
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

        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700 }}>Content Niche & Audience</h3>
          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
              Niche
            </label>
            <input
              type="text"
              value={settings.niche}
              onChange={(e) => setSettings({ ...settings, niche: e.target.value })}
              style={{ width: '100%', padding: '8px 12px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', color: '#fff' }}
            />
          </div>
          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
              Target Audience
            </label>
            <input
              type="text"
              value={settings.target_audience}
              onChange={(e) => setSettings({ ...settings, target_audience: e.target.value })}
              style={{ width: '100%', padding: '8px 12px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-sm)', color: '#fff' }}
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
