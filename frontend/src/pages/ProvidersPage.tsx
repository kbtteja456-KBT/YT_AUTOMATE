import React from 'react';
import { ProviderHealthGrid } from '../components/ProviderHealthGrid';
import { ProvidersHealthResponse } from '../services/api';

interface ProvidersPageProps {
  healthData: ProvidersHealthResponse | null;
  onRefresh: () => void;
}

export const ProvidersPage: React.FC<ProvidersPageProps> = ({ healthData, onRefresh }) => {
  return (
    <div className="page-body">
      <div className="card" style={{ borderLeft: '4px solid var(--accent-cyan)' }}>
        <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '6px' }}>Zero-Cost Verification Policy</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '13px', lineHeight: 1.5 }}>
          The system strictly enforces the provider priority: Local/Open-Source &gt; Free API &gt; Free OpenRouter models &gt; Licensed Free Stock. Any paid call is halted outright when Zero-Cost Mode is enabled.
        </p>
      </div>

      <ProviderHealthGrid healthData={healthData} onRefresh={onRefresh} />
    </div>
  );
};
