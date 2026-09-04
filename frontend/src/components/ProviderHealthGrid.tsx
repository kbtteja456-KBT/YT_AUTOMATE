import React from 'react';
import { ProvidersHealthResponse } from '../services/api';

interface ProviderHealthGridProps {
  healthData: ProvidersHealthResponse | null;
  onRefresh: () => void;
}

export const ProviderHealthGrid: React.FC<ProviderHealthGridProps> = ({ healthData, onRefresh }) => {
  if (!healthData || !healthData.subsystems) {
    return (
      <div className="card">
        <p style={{ color: 'var(--text-secondary)' }}>Loading provider health telemetry...</p>
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'CONNECTED':
        return <span className="status-pill status-published">Connected</span>;
      case 'NOT_CONFIGURED':
        return <span className="status-pill status-scheduled">Not Configured</span>;
      case 'BLOCKED_ZERO_COST':
        return <span className="status-pill status-missed">Blocked (Zero-Cost)</span>;
      case 'OFFLINE':
      default:
        return <span className="status-pill status-missed">Offline</span>;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '18px' }}>Provider Subsystems</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>
            Real-time connection checks. Never fabricated.
          </p>
        </div>
        <button className="btn btn-secondary" onClick={onRefresh}>
          Refresh Health Checks
        </button>
      </div>

      <div className="provider-grid">
        {Object.entries(healthData.subsystems).map(([key, item]) => (
          <div key={key} className="card provider-card">
            <div className="provider-header">
              <span className="provider-name">{item.provider}</span>
              {getStatusBadge(item.status)}
            </div>
            <div className="provider-msg">{item.message}</div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)' }}>
              <span>Zero-Cost: {item.is_zero_cost ? 'Yes (₹0)' : 'Paid'}</span>
              <span>Subsystem: {key.toUpperCase()}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
