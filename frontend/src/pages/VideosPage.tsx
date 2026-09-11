import React, { useState } from 'react';
import { VideoItem, resolveMediaUrl, api } from '../services/api';
import { TrashIcon } from '../components/Icons';

interface VideosPageProps {
  videos: VideoItem[];
  onGenerateClick: () => void;
  onVideoDeleted?: (id: string) => void;
}

export const VideosPage: React.FC<VideosPageProps> = ({ videos, onGenerateClick, onVideoDeleted }) => {
  const [selectedVideo, setSelectedVideo] = useState<VideoItem | null>(null);
  const [editTitle, setEditTitle] = useState<string>('');
  const [editDescription, setEditDescription] = useState<string>('');
  const [isEditingMetadata, setIsEditingMetadata] = useState<boolean>(false);
  const [isSavingMeta, setIsSavingMeta] = useState<boolean>(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [publishingId, setPublishingId] = useState<string | null>(null);
  const [confirmDeleteVideo, setConfirmDeleteVideo] = useState<VideoItem | null>(null);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);

  const handleOpenVideo = (video: VideoItem) => {
    setSelectedVideo(video);
    setEditTitle(video.title);
    setEditDescription(video.description);
    setIsEditingMetadata(false);
  };

  const handleSaveMetadata = async () => {
    if (!selectedVideo) return;
    setIsSavingMeta(true);
    try {
      const updated = await api.updateVideo(selectedVideo.id, {
        title: editTitle,
        description: editDescription
      });
      setSelectedVideo({
        ...selectedVideo,
        title: updated.title,
        description: updated.description
      });
      setIsEditingMetadata(false);
      setFeedbackMessage('✅ Video title & description updated successfully!');
      setTimeout(() => setFeedbackMessage(null), 3500);
    } catch (err: any) {
      alert(`Failed to update metadata: ${err.message}`);
    } finally {
      setIsSavingMeta(false);
    }
  };


  const handlePublishVideo = async (video: VideoItem) => {
    setPublishingId(video.id);
    setFeedbackMessage(null);
    try {
      const res = await api.publishVideo(video.id);
      setFeedbackMessage(`🎉 Published successfully to your connected YouTube channel!`);
      if (selectedVideo?.id === video.id) {
        setSelectedVideo({
          ...selectedVideo,
          youtube_video_id: res.youtube_video_id,
          youtube_url: res.youtube_url,
          status: 'PUBLISHED'
        });
      }
    } catch (err: any) {
      setFeedbackMessage(`Upload error: ${err.message || 'Failed to publish to YouTube'}`);
    } finally {
      setPublishingId(null);
    }
  };

  const getThumbnailSrc = (video: VideoItem) => {
    if (video.youtube_video_id) {
      return `https://img.youtube.com/vi/${video.youtube_video_id}/hqdefault.jpg`;
    }
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

  const handleDeleteVideo = async (video: VideoItem) => {
    setDeletingId(video.id);
    try {
      await api.deleteVideo(video.id);
      if (selectedVideo?.id === video.id) {
        setSelectedVideo(null);
      }
      setConfirmDeleteVideo(null);
      if (onVideoDeleted) {
        onVideoDeleted(video.id);
      }
      setFeedbackMessage(`Deleted "${video.title || 'Video'}" from database and storage.`);
      setTimeout(() => setFeedbackMessage(null), 4000);
    } catch (err: any) {
      alert(`Failed to delete video: ${err.message}`);
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="page-body">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '22px' }}>Rendered & Published Videos</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '14px' }}>
            Manage rendered 1080x1920 MP4 assets, quality check audits, and published Shorts.
          </p>
        </div>
        <button className="btn btn-primary" onClick={onGenerateClick}>
          + Render New Video
        </button>
      </div>

      {feedbackMessage && (
        <div
          style={{
            padding: '12px 18px',
            borderRadius: '10px',
            background: 'rgba(16, 185, 129, 0.15)',
            border: '1px solid rgba(16, 185, 129, 0.35)',
            color: '#34d399',
            fontSize: '13px',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            animation: 'fadeIn 0.25s ease'
          }}
        >
          <span>✅ {feedbackMessage}</span>
          <button
            onClick={() => setFeedbackMessage(null)}
            style={{ background: 'none', border: 'none', color: '#34d399', cursor: 'pointer', fontSize: '14px' }}
          >
            ✕
          </button>
        </div>
      )}

      {videos.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '60px 20px' }}>
          <div style={{ fontSize: '40px', marginBottom: '12px' }}>🎬</div>
          <h3 style={{ fontSize: '18px', marginBottom: '8px' }}>No Videos in Library</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', maxWidth: '440px', margin: '0 auto 20px auto' }}>
            Videos are rendered autonomously during pre-generation windows or upon manual trigger.
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
              onClick={() => handleOpenVideo(video)}
              style={{ cursor: 'pointer', transition: 'transform 0.2s, box-shadow 0.2s' }}
              title="Click to review and play video"
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
                <button
                  type="button"
                  className="btn-delete-card"
                  onClick={(e) => {
                    e.stopPropagation();
                    setConfirmDeleteVideo(video);
                  }}
                  title="Delete video from library and database"
                >
                  <TrashIcon size={15} color="currentColor" />
                </button>
                <div className="video-duration-badge">{video.duration_seconds.toFixed(0)}s</div>
              </div>
              <div className="video-info">
                <div className="video-title">{video.title}</div>
                <div className="video-meta" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  {video.youtube_video_id ? (
                    <span style={{ color: 'var(--accent-mint)' }}>Published to YouTube</span>
                  ) : (
                    <span style={{ color: 'var(--accent-gold)' }}>Rendered & QC Passed (Ready)</span>
                  )}
                  {video.views !== undefined && video.views > 0 && (
                    <span style={{ color: 'var(--accent-gold)', fontSize: '12px', fontWeight: 600 }}>👁️ {video.views.toLocaleString()} views</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Confirmation Modal for Delete */}
      {confirmDeleteVideo && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.78)',
            backdropFilter: 'blur(6px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1200,
            padding: '20px'
          }}
          onClick={() => !deletingId && setConfirmDeleteVideo(null)}
        >
          <div
            className="card"
            style={{
              maxWidth: '440px',
              width: '100%',
              background: '#0f172a',
              border: '1px solid rgba(239, 68, 68, 0.35)',
              borderRadius: '16px',
              padding: '24px',
              boxShadow: '0 25px 60px rgba(0, 0, 0, 0.85)',
              animation: 'scaleIn 0.2s ease'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '16px' }}>
              <div
                style={{
                  width: '44px',
                  height: '44px',
                  borderRadius: '12px',
                  background: 'rgba(239, 68, 68, 0.15)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#ef4444',
                  flexShrink: 0
                }}
              >
                <TrashIcon size={22} color="#ef4444" />
              </div>
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: 700, margin: 0, color: '#f3f4f6' }}>
                  Delete Video?
                </h3>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  Permanent database & file deletion
                </span>
              </div>
            </div>

            <p style={{ color: 'var(--text-secondary)', fontSize: '13.5px', lineHeight: 1.55, marginBottom: '22px' }}>
              Are you sure you want to delete <strong style={{ color: '#fff' }}>"{confirmDeleteVideo.title}"</strong>?
              This will permanently remove the record from MongoDB Atlas and clean up rendered media files.
            </p>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setConfirmDeleteVideo(null)}
                disabled={!!deletingId}
                style={{ padding: '8px 18px', fontSize: '13px' }}
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn"
                onClick={() => handleDeleteVideo(confirmDeleteVideo)}
                disabled={!!deletingId}
                style={{
                  background: 'linear-gradient(135deg, #ef4444 0%, #b91c1c 100%)',
                  color: '#ffffff',
                  fontWeight: 600,
                  padding: '8px 20px',
                  fontSize: '13px',
                  borderRadius: '8px',
                  border: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  cursor: deletingId ? 'wait' : 'pointer',
                  boxShadow: '0 4px 14px rgba(239, 68, 68, 0.4)'
                }}
              >
                <TrashIcon size={15} color="#ffffff" />
                {deletingId === confirmDeleteVideo.id ? 'Deleting...' : 'Delete Video'}
              </button>
            </div>
          </div>
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
              maxWidth: '540px',
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
              <div>
                <span
                  style={{
                    display: 'inline-block',
                    padding: '3px 8px',
                    borderRadius: '6px',
                    fontSize: '11px',
                    fontWeight: 700,
                    marginBottom: '6px',
                    background: selectedVideo.youtube_url ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.2)',
                    color: selectedVideo.youtube_url ? '#34d399' : '#fbbf24',
                    border: `1px solid ${selectedVideo.youtube_url ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.4)'}`
                  }}
                >
                  {selectedVideo.youtube_url ? '🟢 LIVE ON YOUTUBE' : '🟡 READY FOR REVIEW & EDIT'}
                </span>
                <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#f3f4f6', margin: 0 }}>
                  {selectedVideo.title}
                </h3>
              </div>
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

            <div style={{ background: '#000', borderRadius: '12px', overflow: 'hidden', display: 'flex', justifyContent: 'center', minHeight: '380px', position: 'relative' }}>
              {selectedVideo.youtube_video_id ? (
                <iframe
                  src={`https://www.youtube.com/embed/${selectedVideo.youtube_video_id}?autoplay=1&rel=0`}
                  title={selectedVideo.title}
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                  allowFullScreen
                  style={{
                    width: '100%',
                    height: '460px',
                    border: 'none',
                    borderRadius: '12px'
                  }}
                />
              ) : (
                <video
                  controls
                  autoPlay
                  src={getVideoSrc(selectedVideo)}
                  style={{ maxHeight: '460px', width: 'auto', borderRadius: '12px' }}
                />
              )}
            </div>

            {/* Review & Edit Studio Section */}
            <div
              style={{
                background: 'rgba(15, 23, 42, 0.7)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                borderRadius: '12px',
                padding: '14px',
                display: 'flex',
                flexDirection: 'column',
                gap: '10px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '12px', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  📝 Video Metadata & Details
                </span>
                {!selectedVideo.youtube_url && (
                  <button
                    type="button"
                    onClick={() => setIsEditingMetadata(!isEditingMetadata)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#60a5fa',
                      fontSize: '12px',
                      fontWeight: 600,
                      cursor: 'pointer'
                    }}
                  >
                    {isEditingMetadata ? 'Cancel Editing' : '✏️ Edit Title & Description'}
                  </button>
                )}
              </div>

              {isEditingMetadata ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>Title</label>
                    <input
                      type="text"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      maxLength={100}
                      style={{
                        width: '100%',
                        boxSizing: 'border-box',
                        padding: '8px 10px',
                        background: '#1e293b',
                        border: '1px solid #3b82f6',
                        borderRadius: '8px',
                        color: '#fff',
                        fontSize: '13px'
                      }}
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>Description</label>
                    <textarea
                      value={editDescription}
                      onChange={(e) => setEditDescription(e.target.value)}
                      rows={3}
                      style={{
                        width: '100%',
                        boxSizing: 'border-box',
                        padding: '8px 10px',
                        background: '#1e293b',
                        border: '1px solid #3b82f6',
                        borderRadius: '8px',
                        color: '#fff',
                        fontSize: '12px',
                        lineHeight: 1.4,
                        resize: 'vertical'
                      }}
                    />
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                    <button
                      type="button"
                      onClick={handleSaveMetadata}
                      disabled={isSavingMeta}
                      style={{
                        padding: '6px 14px',
                        background: '#2563eb',
                        border: 'none',
                        color: '#fff',
                        borderRadius: '6px',
                        fontSize: '12px',
                        fontWeight: 600,
                        cursor: isSavingMeta ? 'wait' : 'pointer'
                      }}
                    >
                      {isSavingMeta ? 'Saving...' : '💾 Save Changes'}
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: '#e2e8f0' }}>{selectedVideo.title}</div>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '12px', lineHeight: 1.4, margin: 0, maxHeight: '80px', overflowY: 'auto' }}>
                    {selectedVideo.description}
                  </p>
                </>
              )}
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '10px', borderTop: '1px solid rgba(255, 255, 255, 0.1)', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ display: 'flex', gap: '8px' }}>
                <span className="badge" style={{ background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-mint)', padding: '4px 8px', borderRadius: '6px', fontSize: '12px' }}>
                  QC {selectedVideo.quality_score.toFixed(0)}/100
                </span>
                <span className="badge" style={{ background: 'rgba(255, 255, 255, 0.08)', color: 'var(--accent-titanium)', padding: '4px 8px', borderRadius: '6px', fontSize: '12px' }}>
                  {selectedVideo.duration_seconds.toFixed(0)}s Short
                </span>
                {selectedVideo.views !== undefined && (
                  <span className="badge" style={{ background: 'rgba(245, 158, 11, 0.15)', color: 'var(--accent-gold)', padding: '4px 8px', borderRadius: '6px', fontSize: '12px' }}>
                    👁️ {selectedVideo.views.toLocaleString()} views
                  </span>
                )}
              </div>

              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
                <button
                  type="button"
                  className="btn"
                  onClick={() => setConfirmDeleteVideo(selectedVideo)}
                  style={{
                    background: 'rgba(239, 68, 68, 0.15)',
                    border: '1px solid rgba(239, 68, 68, 0.4)',
                    color: '#f87171',
                    padding: '6px 12px',
                    fontSize: '13px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    borderRadius: '8px',
                    cursor: 'pointer'
                  }}
                  title="Delete video from database"
                >
                  <TrashIcon size={14} color="#f87171" />
                  Delete
                </button>
                {!selectedVideo.youtube_url && (
                  <button
                    type="button"
                    className="btn btn-primary"
                    disabled={publishingId === selectedVideo.id}
                    onClick={() => handlePublishVideo(selectedVideo)}
                    style={{
                      padding: '8px 16px',
                      fontSize: '13px',
                      fontWeight: 700,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      borderRadius: '8px',
                      background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                      boxShadow: '0 4px 14px rgba(16, 185, 129, 0.4)',
                      cursor: publishingId === selectedVideo.id ? 'not-allowed' : 'pointer'
                    }}
                    title="Upload and publish directly to your connected YouTube channel"
                  >
                    {publishingId === selectedVideo.id ? '⏳ Uploading...' : '🚀 Publish to YouTube'}
                  </button>
                )}
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
                    ▶ Watch on Shorts
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
