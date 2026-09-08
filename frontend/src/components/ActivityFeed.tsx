import React from 'react';
import { ActivityEventItem } from '../services/api';
import { CheckCircleIcon } from './Icons';

interface ActivityFeedProps {
  events: ActivityEventItem[];
}

export const ActivityFeed: React.FC<ActivityFeedProps> = ({ events }) => {
  const latestEvent = events[0];
  const latestMsg = latestEvent?.message || 'Pipeline idle. Ready to create your first short.';
  const latestTime = latestEvent?.timestamp
    ? new Date(latestEvent.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    : 'Ready';

  // Check if a job is actively running right now
  const isPipelineActive = latestEvent?.event_type === 'PIPELINE_ACTIVE';
  const rawStage = (latestEvent?.stage || '').toUpperCase();

  let activeIndex = -1;
  if (isPipelineActive) {
    if (rawStage.includes('RESEARCH')) activeIndex = 0;
    else if (rawStage.includes('SCRIPT')) activeIndex = 1;
    else if (rawStage.includes('VOICE')) activeIndex = 2;
    else if (rawStage.includes('CAPTION') || rawStage.includes('TRANSCRIB')) activeIndex = 3;
    else if (rawStage.includes('RENDER')) activeIndex = 4;
    else if (rawStage.includes('QC') || rawStage.includes('QUALITY')) activeIndex = 5;
    else if (rawStage.includes('UPLOAD') || rawStage.includes('PUBLISH') || rawStage.includes('READY')) activeIndex = 6;
    else activeIndex = 0;
  }

  // Check if recently completed
  const isRecentlyCompleted = latestEvent?.event_type === 'VIDEO_PUBLISHED' || latestEvent?.event_type === 'VIDEO_RENDERED';

  const getStageState = (idx: number): { status: 'done' | 'active' | 'waiting'; statusLabel: string } => {
    if (isPipelineActive) {
      if (idx < activeIndex) return { status: 'done', statusLabel: 'Done' };
      if (idx === activeIndex) return { status: 'active', statusLabel: 'In Progress' };
      return { status: 'waiting', statusLabel: 'Queued' };
    }
    if (isRecentlyCompleted) {
      return { status: 'done', statusLabel: 'Done' };
    }
    return { status: 'waiting', statusLabel: 'Ready' };
  };

  const stages = [
    {
      id: 'research',
      name: 'Research',
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
      ),
      ...getStageState(0)
    },
    {
      id: 'script',
      name: 'Script',
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
        </svg>
      ),
      ...getStageState(1)
    },
    {
      id: 'voice',
      name: 'Voice',
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
          <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
          <line x1="12" y1="19" x2="12" y2="22" />
        </svg>
      ),
      ...getStageState(2)
    },
    {
      id: 'captions',
      name: 'Captions',
      icon: (
        <span style={{ fontWeight: 800, fontSize: '17px', fontFamily: 'var(--font-display)' }}>T</span>
      ),
      ...getStageState(3)
    },
    {
      id: 'rendering',
      name: 'Rendering',
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
          <polygon points="6 4 20 12 6 20 6 4" />
        </svg>
      ),
      ...getStageState(4)
    },
    {
      id: 'qc',
      name: 'QC',
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        </svg>
      ),
      ...getStageState(5)
    },
    {
      id: 'upload',
      name: 'Upload',
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242" />
          <path d="M12 12v9" />
          <path d="m8 16 4-4 4 4" />
        </svg>
      ),
      ...getStageState(6)
    }
  ];

  return (
    <div className="card pipeline-card">
      <div className="pipeline-header">
        <div className="pipeline-title-group">
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: isPipelineActive ? '#3b82f6' : '#10b981',
            boxShadow: isPipelineActive ? '0 0 10px #3b82f6' : '0 0 8px #10b981'
          }} />
          <h3 className="pipeline-title">
            {isPipelineActive ? 'Live Pipeline Activity (Running)' : 'Live Pipeline Activity'}
          </h3>
        </div>
        <div className="live-stream-badge">
          <span style={{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            background: isPipelineActive ? '#3b82f6' : '#10b981',
            display: 'inline-block'
          }} />
          {isPipelineActive ? 'Active Job' : (isRecentlyCompleted ? 'Ready' : 'Idle')}
        </div>
      </div>

      <div className="pipeline-track">
        {stages.map((stage, idx) => {
          let circleClass = 'stage-waiting';
          let statusClass = 'status-text-waiting';
          if (stage.status === 'done') {
            circleClass = 'stage-done';
            statusClass = 'status-text-done';
          } else if (stage.status === 'active') {
            circleClass = 'stage-active';
            statusClass = 'status-text-active';
          }

          return (
            <React.Fragment key={stage.id}>
              <div className="pipeline-stage-item">
                <div className={`pipeline-stage-circle ${circleClass}`}>
                  {stage.icon}
                </div>
                <span className="pipeline-stage-name">{stage.name}</span>
                <span className={`pipeline-stage-status ${statusClass}`}>
                  {stage.status === 'done' && <CheckCircleIcon size={11} color="#10b981" />}
                  {stage.statusLabel}
                </span>
              </div>
              {idx < stages.length - 1 && (
                <span className="pipeline-connector-arrow">→</span>
              )}
            </React.Fragment>
          );
        })}
      </div>

      <div className="pipeline-ticker-bar">
        <div className="ticker-left">
          <div className="ticker-icon-box">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="#ffffff">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
            </svg>
          </div>
          <span className="ticker-message">{latestMsg}</span>
        </div>
        <span className="ticker-time">{latestTime}</span>
      </div>
    </div>
  );
};
