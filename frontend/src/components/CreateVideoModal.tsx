import React, { useState } from 'react';
import { api } from '../services/api';

interface CreateVideoModalProps {
  isOpen: boolean;
  onClose: () => void;
  onVideoQueued: (jobId: string) => void;
  defaultNiche?: string;
  hasConnectedChannel?: boolean;
}

interface Preset {
  label: string;
  emoji: string;
  format: string;
  prompt: string;
}

const PRESETS: Preset[] = [
  {
    label: 'Tech & AI News',
    emoji: '⚡',
    format: 'documentary',
    prompt: 'An informational video about the latest tech news and autonomous AI agent breakthroughs in 2025'
  },
  {
    label: 'Deep Science',
    emoji: '🔬',
    format: 'documentary',
    prompt: 'The mind-blowing turning point in quantum computing error correction and commercial quantum supremacy'
  },
  {
    label: 'Humanoid Robotics',
    emoji: '🤖',
    format: 'documentary',
    prompt: 'How humanoid robots are officially stepping out of research labs and into live automotive factories'
  },
  {
    label: 'Python Quiz',
    emoji: '🐍',
    format: 'quiz_card',
    prompt: 'Python Quiz: List mutation and aliasing tricky question #Shorts'
  },
  {
    label: 'Java Quiz',
    emoji: '☕',
    format: 'quiz_card',
    prompt: 'Java Quiz: String == vs .equals() object reference trap #Shorts'
  },
  {
    label: 'Stoic Wisdom',
    emoji: '🏛️',
    format: 'quote_card',
    prompt: 'Stoic Wisdom: Marcus Aurelius on mastering your mind instead of stressing over external chaos'
  },
  {
    label: 'Fun Trivia',
    emoji: '🧠',
    format: 'trivia_quiz',
    prompt: 'Trivia Quiz: Which planet in our solar system has the most confirmed moons? #Shorts'
  }
];

export const CreateVideoModal: React.FC<CreateVideoModalProps> = ({
  isOpen,
  onClose,
  onVideoQueued,
  defaultNiche: _defaultNiche,
  hasConnectedChannel = false
}) => {
  const [prompt, setPrompt] = useState<string>('');
  const [contentFormat, setContentFormat] = useState<string>('auto');
  const [duration, setDuration] = useState<number>(45);
  const [autoPublish, setAutoPublish] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleApplyPreset = (preset: Preset) => {
    setPrompt(preset.prompt);
    setContentFormat(preset.format);
    setErrorMsg(null);
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      const res = await api.triggerGenerate({
        prompt: prompt.trim() || undefined,
        topic: prompt.trim() ? prompt.trim().slice(0, 60) : undefined,
        content_format: contentFormat,
        duration,
        auto_publish: autoPublish && hasConnectedChannel
      });

      onVideoQueued(res.job_id);
      onClose();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to queue video generation');
      setIsSubmitting(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(3, 7, 18, 0.85)',
        backdropFilter: 'blur(10px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1100,
        padding: '16px',
        animation: 'fadeIn 0.2s ease-out'
      }}
      onClick={onClose}
    >
      <div
        style={{
          maxWidth: '640px',
          width: '100%',
          background: 'linear-gradient(180deg, #0f172a 0%, #090d16 100%)',
          border: '1px solid rgba(59, 130, 246, 0.3)',
          borderRadius: '20px',
          padding: '28px',
          boxShadow: '0 25px 60px -15px rgba(0, 0, 0, 0.9), 0 0 35px rgba(59, 130, 246, 0.15)',
          color: '#f8fafc',
          maxHeight: '90vh',
          overflowY: 'auto'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '24px' }}>✨</span>
              <h2 style={{ fontSize: '20px', fontWeight: 700, margin: 0, background: 'linear-gradient(90deg, #60a5fa, #a78bfa)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                Universal Prompt-to-Video Engine
              </h2>
            </div>
            <p style={{ color: '#94a3b8', fontSize: '13px', margin: '6px 0 0 0', lineHeight: 1.5 }}>
              Describe any concept or news topic. The AI automatically analyzes the requirements, writes the script, acquires real stock visuals, synthesizes voiceover and captions, and renders a vertical 1080x1920 Short.
            </p>
          </div>
          <button
            onClick={onClose}
            disabled={isSubmitting}
            style={{
              background: 'rgba(255, 255, 255, 0.08)',
              border: 'none',
              color: '#94a3b8',
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              cursor: 'pointer',
              fontSize: '16px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0
            }}
          >
            ✕
          </button>
        </div>

        {errorMsg && (
          <div
            style={{
              padding: '12px 16px',
              borderRadius: '10px',
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.35)',
              color: '#fca5a5',
              fontSize: '13px',
              marginBottom: '16px'
            }}
          >
            ⚠️ {errorMsg}
          </div>
        )}

        <form onSubmit={handleGenerate} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          {/* Prompt Input */}
          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#cbd5e1', marginBottom: '8px' }}>
              What do you want to create? <span style={{ color: '#60a5fa' }}>*</span>
            </label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g., An informational video about the latest tech news and AI breakthroughs, or a Java tricky quiz, or Marcus Aurelius stoic mindset..."
              rows={3}
              style={{
                width: '100%',
                boxSizing: 'border-box',
                padding: '14px',
                borderRadius: '12px',
                background: 'rgba(15, 23, 42, 0.8)',
                border: '1px solid rgba(148, 163, 184, 0.2)',
                color: '#f8fafc',
                fontSize: '14px',
                lineHeight: 1.5,
                resize: 'vertical',
                outline: 'none',
                fontFamily: 'inherit'
              }}
              onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
              onBlur={(e) => (e.target.style.borderColor = 'rgba(148, 163, 184, 0.2)')}
            />
          </div>

          {/* Preset Inspiration Chips */}
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#94a3b8', marginBottom: '8px' }}>
              💡 Quick Inspiration Presets:
            </label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {PRESETS.map((p) => (
                <button
                  type="button"
                  key={p.label}
                  onClick={() => handleApplyPreset(p)}
                  style={{
                    background: prompt === p.prompt ? 'rgba(59, 130, 246, 0.25)' : 'rgba(255, 255, 255, 0.05)',
                    border: `1px solid ${prompt === p.prompt ? '#3b82f6' : 'rgba(255, 255, 255, 0.1)'}`,
                    color: prompt === p.prompt ? '#93c5fd' : '#cbd5e1',
                    borderRadius: '20px',
                    padding: '5px 12px',
                    fontSize: '12px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '5px',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <span>{p.emoji}</span>
                  <span>{p.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Grid: Format & Duration */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#cbd5e1', marginBottom: '6px' }}>
                Content Format
              </label>
              <select
                value={contentFormat}
                onChange={(e) => setContentFormat(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  borderRadius: '10px',
                  background: '#1e293b',
                  border: '1px solid rgba(148, 163, 184, 0.2)',
                  color: '#f8fafc',
                  fontSize: '13px',
                  outline: 'none',
                  cursor: 'pointer'
                }}
              >
                <option value="auto">✨ Auto-Detect from Prompt</option>
                <option value="documentary">📹 Documentary & Stories (Hybrid Videos & Photos)</option>
                <option value="quiz_card">💻 Code Quiz Challenge (Interactive Syntax Card)</option>
                <option value="quote_card">🏛️ Daily Motivation & Wisdom (Quote Card)</option>
                <option value="trivia_quiz">🧠 Trivia Riddle & Brain Teaser (Question Card)</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#cbd5e1', marginBottom: '6px' }}>
                Duration
              </label>
              <div style={{ display: 'flex', gap: '8px' }}>
                {[30, 45, 60].map((sec) => (
                  <button
                    type="button"
                    key={sec}
                    onClick={() => setDuration(sec)}
                    style={{
                      flex: 1,
                      padding: '10px 0',
                      borderRadius: '10px',
                      background: duration === sec ? '#2563eb' : '#1e293b',
                      border: `1px solid ${duration === sec ? '#3b82f6' : 'rgba(255, 255, 255, 0.1)'}`,
                      color: '#ffffff',
                      fontSize: '13px',
                      fontWeight: 600,
                      cursor: 'pointer',
                      transition: 'background 0.15s ease'
                    }}
                  >
                    {sec}s
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Review Before Publishing Option */}
          <div
            style={{
              padding: '14px 16px',
              borderRadius: '12px',
              background: 'rgba(30, 41, 59, 0.6)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '12px'
            }}
          >
            <input
              type="checkbox"
              id="autoPublishCheckbox"
              checked={autoPublish}
              onChange={(e) => setAutoPublish(e.target.checked)}
              disabled={!hasConnectedChannel}
              style={{ marginTop: '3px', cursor: hasConnectedChannel ? 'pointer' : 'not-allowed', width: '16px', height: '16px' }}
            />
            <label htmlFor="autoPublishCheckbox" style={{ fontSize: '13px', color: '#e2e8f0', cursor: hasConnectedChannel ? 'pointer' : 'default' }}>
              <span style={{ fontWeight: 600 }}>Auto-Publish to connected YouTube channel immediately upon render</span>
              <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: '#94a3b8', lineHeight: 1.4 }}>
                {hasConnectedChannel
                  ? 'Keep unchecked (recommended) to preview your video first, review and edit title/description, and publish with 1 click.'
                  : 'Connect your YouTube channel in settings to enable direct 1-click publishing.'}
              </p>
            </label>
          </div>

          {/* Hybrid Engine Feature Note */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 14px',
              borderRadius: '10px',
              background: 'rgba(59, 130, 246, 0.08)',
              border: '1px solid rgba(59, 130, 246, 0.2)',
              fontSize: '12px',
              color: '#93c5fd'
            }}
          >
            <span>🎬</span>
            <span>
              <strong>Hybrid Visual Engine:</strong> Intelligently alternates high-energy motion video clips and cinematic high-res photos (with Ken Burns zoom/pan) to match your concept.
            </span>
          </div>

          {/* Submit Actions */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '8px' }}>
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              style={{
                padding: '10px 18px',
                borderRadius: '10px',
                background: 'rgba(255, 255, 255, 0.08)',
                border: 'none',
                color: '#cbd5e1',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              style={{
                padding: '10px 24px',
                borderRadius: '10px',
                background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
                border: 'none',
                color: '#ffffff',
                fontSize: '13px',
                fontWeight: 700,
                cursor: isSubmitting ? 'wait' : 'pointer',
                boxShadow: '0 4px 18px rgba(59, 130, 246, 0.4)',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              {isSubmitting ? (
                <>
                  <span style={{ animation: 'spin 1s linear infinite' }}>⏳</span>
                  <span>Queueing Studio Engine...</span>
                </>
              ) : (
                <>
                  <span>🚀</span>
                  <span>Generate Video Short</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
