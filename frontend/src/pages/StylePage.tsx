import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

export const StylePage: React.FC = () => {
  const [profile, setProfile] = useState<any>(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const data = await api.getStyleProfile();
      setProfile(data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setMessage(null);
    try {
      const res = await api.uploadReferenceVideo(file);
      setMessage(`Success: ${res.message}`);
      await loadProfile();
    } catch (err: any) {
      setMessage(`Error: ${err.message || 'Upload failed'}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="page-body">
      <div>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '22px' }}>Reference Video Style Analyzer</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '14px' }}>
          Ingests a ~44-second vertical Short to extract dual-segment editing rhythm (handheld demo + screen walkthrough).
        </p>
      </div>

      <div className="card" style={{ borderLeft: '4px solid var(--accent-purple)' }}>
        <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '6px' }}>Strict Pacing Extraction Only</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '13px', lineHeight: 1.5 }}>
          The analyzer extracts pacing ratios, cut frequency, and caption typography. Never reuses face, voice, footage, or script from the reference video.
        </p>
      </div>

      <div className="two-col-grid">
        <div className="card">
          <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '16px' }}>Active Style Blueprint</h3>
          {profile ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Target Duration:</span>
                <span style={{ fontWeight: 600 }}>{profile.total_duration_sec}s</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Segment Pacing Split:</span>
                <span style={{ fontWeight: 600 }}>
                  {(profile.real_footage_ratio * 100).toFixed(0)}% Real Demo / {(profile.screen_recording_ratio * 100).toFixed(0)}% Screen
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Average Cut Frequency:</span>
                <span style={{ fontWeight: 600 }}>Every {profile.cut_frequency_sec}s</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Opening Hook Scene Duration:</span>
                <span style={{ fontWeight: 600 }}>{profile.hook_duration_sec}s</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--text-muted)' }}>Caption Highlight Accent:</span>
                <span style={{ fontWeight: 600, color: profile.caption_highlight_color }}>
                  {profile.caption_highlight_color}
                </span>
              </div>
            </div>
          ) : (
            <p>Loading style parameters...</p>
          )}
        </div>

        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700 }}>Upload New Reference Short</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
            Upload a 9:16 vertical Short (.mp4, .mov) to calibrate the visual density and shot rhythm.
          </p>
          <div style={{ border: '2px dashed var(--border-subtle)', borderRadius: 'var(--radius-sm)', padding: '28px', textAlign: 'center' }}>
            <input
              type="file"
              accept="video/*"
              id="ref-video-input"
              style={{ display: 'none' }}
              onChange={handleFileUpload}
            />
            <label htmlFor="ref-video-input" className="btn btn-secondary" style={{ cursor: 'pointer' }}>
              {uploading ? 'Analyzing Video...' : 'Select Video File'}
            </label>
          </div>
          {message && (
            <div style={{ fontSize: '13px', color: message.startsWith('Error') ? 'var(--accent-rose)' : 'var(--accent-mint)' }}>
              {message}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
