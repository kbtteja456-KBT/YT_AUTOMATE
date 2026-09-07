import React from 'react';
import { AutopilotStatusResponse } from '../services/api';
import { CalendarBlueTileIcon, CheckCircleIcon, ClockIcon, PauseIcon, PlayIcon } from './Icons';

interface AutopilotHeroProps {
  status: AutopilotStatusResponse | null;
  onToggle: () => void;
}

export const AutopilotHero: React.FC<AutopilotHeroProps> = ({ status, onToggle }) => {
  const isEnabled = status?.is_enabled ?? true;

  const getSlot1Status = () => {
    return (status?.status_today?.slot_1 || 'PUBLISHED').toUpperCase();
  };

  const getSlot2Status = () => {
    return (status?.status_today?.slot_2 || 'SCHEDULED').toUpperCase();
  };

  const renderSlotBadge = (statusStr: string) => {
    if (statusStr === 'PUBLISHED') {
      return (
        <span className="status-badge-published">
          <CheckCircleIcon size={12} color="#10b981" />
          Published
        </span>
      );
    }
    return (
      <span className="status-badge-scheduled">
        <ClockIcon size={12} color="#60a5fa" />
        {statusStr === 'PENDING' ? 'Scheduled' : statusStr}
      </span>
    );
  };

  return (
    <div className="card autopilot-hero-3d">
      <div className="hero-left-section">
        <div style={{ flexShrink: 0 }}>
          <CalendarBlueTileIcon size={48} />
        </div>
        <div className="hero-content-col">
          <h2>Autonomous Daily Publishing</h2>
          <p>
            Target: 2 original 1080x1920 Shorts daily at 07:00 & 18:00 ({status?.timezone || 'Asia/Kolkata'}).<br />
            Pre-generation windows run 01:00–06:30 and 12:00–17:30.
          </p>
          <div className="hero-slots-row">
            <div className="slot-pill-3d">
              <span>☀️ Morning Slot (07:00)</span>
              {renderSlotBadge(getSlot1Status())}
            </div>
            <div className="slot-pill-3d">
              <span>🌙 Evening Slot (18:00)</span>
              {renderSlotBadge(getSlot2Status())}
            </div>
          </div>
        </div>
      </div>

      <div className="hero-right-section">
        <div className="robot-mascot-wrapper">
          <div className="robot-speech-bubble">
            Creating Better Shorts Everyday!
          </div>
          <img
            src="/mascot.jpg"
            alt="Shorts Autopilot Mascot"
            className="robot-mascot-img"
            onError={(e) => {
              (e.target as HTMLElement).style.display = 'none';
            }}
          />
        </div>

        <button
          className={`btn hero-pause-btn ${isEnabled ? 'btn-danger' : 'btn-primary'}`}
          onClick={onToggle}
        >
          {isEnabled ? (
            <>
              <PauseIcon size={15} />
              <span>Pause Autopilot</span>
            </>
          ) : (
            <>
              <PlayIcon size={15} />
              <span>Resume Autopilot</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
