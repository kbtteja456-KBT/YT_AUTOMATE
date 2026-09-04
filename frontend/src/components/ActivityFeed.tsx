import React from 'react';
import { ActivityEventItem } from '../services/api';

interface ActivityFeedProps {
  events: ActivityEventItem[];
}

export const ActivityFeed: React.FC<ActivityFeedProps> = ({ events }) => {
  return (
    <div className="card">
      <div className="stat-header" style={{ marginBottom: '16px' }}>
        <span style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)' }}>
          Live Pipeline Activity
        </span>
        <span className="status-pill status-preparing">Live Stream</span>
      </div>

      <div className="activity-feed">
        {events.length === 0 ? (
          <div style={{ color: 'var(--text-muted)', fontSize: '13px', padding: '16px 0' }}>
            No recent pipeline events. Waiting for scheduled window or manual trigger.
          </div>
        ) : (
          events.map((ev, i) => (
            <div key={ev.id || i} className="activity-item">
              <div className="activity-icon-box">⚡</div>
              <div className="activity-details">
                <div className="activity-title">{ev.message}</div>
                <div className="activity-time">
                  {ev.agent_name ? `[${ev.agent_name}] • ` : ''}
                  {new Date(ev.timestamp).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
