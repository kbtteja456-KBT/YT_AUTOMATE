import React, { useState } from 'react';
import { VideoItem, resolveMediaUrl } from '../services/api';

interface VideosPageProps {
  videos: VideoItem[];
  onGenerateClick: () => void;
}

export const VideosPage: React.FC<VideosPageProps> = ({ videos, onGenerateClick }) => {
  const [selectedVideo, setSelectedVideo] = useState<VideoItem | null>(null);

  const getThumbnailSrc = (video: VideoItem) => {
    if (video.thumbnail_url) return resolveMediaUrl(video.thumbnail_url);
    if (video.thumbnail_path && (video.thumbnail_path.startsWith('http') || video.thumbnail_path.startsWith('/'))) {
      return resolveMediaUrl(video.thumbnail_path);
    }
    return resolveMediaUrl('/media/thumbnails/thumb_test.jpg');
  };

  const getVideoSrc = (video: VideoItem) => {
    if (video.video_url) return resolveMediaUrl(video.video_url);
    if (video.file_path && (video.file_path.startsWith('http') || video.file_path.startsWith('/'))) {
      return resolveMediaUrl(video.file_path);
    }
    return resolveMediaUrl('/media/rendered/short_rendered.mp4');
  };

  return (
    <div className="page-body">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '22px' }}>Rendered & Published Videos</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '14px' }}>
            Real 1080x1920 MP4 assets produced by the local FFmpeg rendering engine.
          </p>
        </div>
        <button className="btn btn-primary" onClick={onGenerateClick}>
          + Render New Video
        </button>
      </div>

      {videos.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '60px 20px' }}>
          <div style={{ fontSize: '40px', marginBottom: '12px' }}>🎬</div>
          <h3 style={{ fontSize: '18px', marginBottom: '8px' }}>No Videos Rendered Yet</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', maxWidth: '440px', margin: '0 auto 20px auto' }}>
            Videos are rendered autonomously during pre-generation windows (01:00-06:30 & 12:00-17:30) or upon manual trigger.
          </p>
          <button className="btn btn-primary" onClick={onGenerateClick}>
            Trigger First Video Run
          </button>
        </div>
      ) : (
        <div className="video-grid">
          {videos.map((video) => (
            <div
              key={video.id}
              className="video-card"
              onClick={() => setSelectedVideo(video)}
              style={{ cursor: 'pointer', transition: 'transform 0.2s, box-shadow 0.2s' }}
              title="Click to play video"
            >
              <div className="video-thumbnail-wrapper" style={{ position: 'relative' }}>
                <img
                  src={getThumbnailSrc(video)}
                  alt={video.title}
                  className="video-thumbnail"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = '/media/thumbnails/thumb_test.jpg';
                  }}
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
                <div
                  style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    width: '54px',
                    height: '54px',
                    borderRadius: '50%',
                    background: 'rgba(0, 0, 0, 0.65)',
                    backdropFilter: 'blur(4px)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '22px',
                    color: '#fff',
                    border: '2px solid rgba(255, 255, 255, 0.4)',
                    boxShadow: '0 4px 16px rgba(0,0,0,0.5)'
                  }}
                >
                  ▶
                </div>
                <div className="video-qc-badge">QC: {video.quality_score.toFixed(0)}/100</div>
                <div className="video-duration-badge">{video.duration_seconds.toFixed(0)}s</div>
              </div>
              <div className="video-info">
                <div className="video-title">{video.title}</div>
                <div className="video-meta">
                  {video.youtube_video_id ? (
                    <span style={{ color: 'var(--accent-mint)' }}>Published to YouTube</span>
                  ) : (
                    <span style={{ color: 'var(--accent-cyan)' }}>Rendered & QC Passed (Ready)</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Video Player Modal */}
      {selectedVideo && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.85)',
            backdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '20px'
          }}
          onClick={() => setSelectedVideo(null)}
        >
          <div
            className="card"
            style={{
              maxWidth: '520px',
              width: '100%',
              background: '#0f172a',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              borderRadius: '16px',
              padding: '20px',
              display: 'flex',
              flexDirection: 'column',
              gap: '14px',
              boxShadow: '0 20px 50px rgba(0,0,0,0.8)'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#f3f4f6' }}>
                {selectedVideo.title}
              </h3>
              <button
                onClick={() => setSelectedVideo(null)}
                style={{
                  background: 'rgba(255, 255, 255, 0.1)',
                  border: 'none',
                  color: '#fff',
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  cursor: 'pointer',
                  fontSize: '16px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                ✕
              </button>
            </div>

            <div style={{ background: '#000', borderRadius: '12px', overflow: 'hidden', display: 'flex', justifyContent: 'center' }}>
              <video
                controls
                autoPlay
                src={getVideoSrc(selectedVideo)}
                style={{ maxHeight: '460px', width: 'auto', borderRadius: '12px' }}
              />
            </div>

            <p style={{ color: 'var(--text-secondary)', fontSize: '13px', lineHeight: 1.5, margin: 0 }}>
              {selectedVideo.description}
            </p>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '8px', borderTop: '1px solid rgba(255, 255, 255, 0.1)', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ display: 'flex', gap: '8px' }}>
                <span className="badge" style={{ background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-mint)', padding: '4px 8px', borderRadius: '6px', fontSize: '12px' }}>
                  QC {selectedVideo.quality_score.toFixed(0)}/100
                </span>
                <span className="badge" style={{ background: 'rgba(99, 102, 241, 0.15)', color: '#a5b4fc', padding: '4px 8px', borderRadius: '6px', fontSize: '12px' }}>
                  {selectedVideo.duration_seconds.toFixed(0)}s Short
                </span>
              </div>

              <div style={{ display: 'flex', gap: '8px' }}>
                {selectedVideo.youtube_url && (
                  <a
                    href={selectedVideo.youtube_url}
                    target="_blank"
                    rel="noreferrer"
                    className="btn"
                    style={{
                      background: '#ff0000',
                      color: '#ffffff',
                      fontWeight: 600,
                      padding: '6px 14px',
                      fontSize: '13px',
                      textDecoration: 'none',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      borderRadius: '8px'
                    }}
                  >
                    ▶ Watch on YouTube Shorts
                  </a>
                )}
                <a
                  href={getVideoSrc(selectedVideo)}
                  download={`short_${selectedVideo.id}.mp4`}
                  className="btn btn-secondary"
                  style={{ padding: '6px 14px', fontSize: '13px', textDecoration: 'none' }}
                >
                  ⬇ Download MP4
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
