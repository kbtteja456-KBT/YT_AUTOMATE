import React from 'react';
import { AutopilotStatusResponse } from '../services/api';

interface AutopilotHeroProps {
  status: AutopilotStatusResponse | null;
  onToggle: () => void;
}

export const AutopilotHero: React.FC<AutopilotHeroProps> = ({ status, onToggle }) => {
  const isEnabled = status?.is_enabled ?? true;

  const renderStatusPill = (statusStr: string) => {
    switch (statusStr.toUpperCase()) {
      case 'PUBLISHED':
        return <span className="status-pill status-published">Published</span>;
      case 'PREPARING':
        return <span className="status-pill status-preparing">Preparing</span>;
      case 'SCHEDULED':
      case 'PENDING':
        return <span className="status-pill status-scheduled">Scheduled</span>;
      case 'MISSED':
      default:
        return <span className="status-pill status-missed">{statusStr}</span>;
    }
  };

  return (
    <div className="card autopilot-hero">
      <div className="hero-info">
        <h2>Autonomous Daily Publishing</h2>
        <p>
          Target: 2 original 1080x1920 Shorts daily at 07:00 & 18:00 ({status?.timezone || 'Asia/Kolkata'}).
          Pre-generation windows run 01:00-06:30 and 12:00-17:30.
        </p>
        <div className="hero-slots">
          <div className="slot-badge">
            <span>Morning Slot (07:00):</span>
            {renderStatusPill(status?.status_today?.slot_1 || 'PREPARING')}
          </div>
          <div className="slot-badge">
            <span>Evening Slot (18:00):</span>
            {renderStatusPill(status?.status_today?.slot_2 || 'PENDING')}
          </div>
        </div>
      </div>

      <div>
        <button
          className={`btn ${isEnabled ? 'btn-danger' : 'btn-primary'}`}
          onClick={onToggle}
        >
          {isEnabled ? 'Pause Autopilot' : 'Resume Autopilot'}
        </button>
      </div>
    </div>
  );
};
