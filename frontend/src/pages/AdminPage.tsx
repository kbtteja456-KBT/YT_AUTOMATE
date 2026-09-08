import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { RefreshIcon } from '../components/Icons';

export const AdminPage: React.FC = () => {
  const [overview, setOverview] = useState<any>(null);
  const [usageData, setUsageData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    loadAdminData();
  }, []);

  const loadAdminData = async () => {
    setLoading(true);
    try {
      const [ov, us] = await Promise.all([
        api.getAdminOverview().catch(() => null),
        api.getAdminUsage().catch(() => null)
      ]);
      setOverview(ov);
      setUsageData(us);
    } catch (e) {
      console.error('Failed to load admin metrics:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleWorkspace = async (workspaceId: string, currentStatus: boolean) => {
    setActionLoading(workspaceId);
    try {
      await api.toggleWorkspace(workspaceId, !currentStatus);
      await loadAdminData();
    } catch (e: any) {
      alert(e.message || 'Action failed');
    } finally {
      setActionLoading(null);
    }
  };

  if (loading && !overview) {
    return (
      <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-secondary)' }}>
        Loading platform cost ledger & tenant metrics...
      </div>
    );
  }

  return (
    <div style={{ padding: '24px 32px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, margin: 0, color: '#f8fafc' }}>
            Platform Cost & Tenant Admin
          </h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Owner oversight on platform key spending, BYOK compliance, and workspace controls.
          </p>
        </div>
        <button
          onClick={loadAdminData}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'rgba(245, 158, 11, 0.15)',
            border: '1px solid rgba(245, 158, 11, 0.35)',
            color: '#f59e0b',
            padding: '8px 16px',
            borderRadius: '10px',
            cursor: 'pointer',
            fontWeight: 600,
            fontSize: '0.8125rem'
          }}
        >
          <RefreshIcon size={14} /> Refresh Metrics
        </button>
      </div>

      {/* Top Stat Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '16px',
        marginBottom: '28px'
      }}>
        <div style={{
          background: 'rgba(24, 29, 40, 0.75)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '16px',
          padding: '20px'
        }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Platform Key Total Cost
          </span>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#f59e0b', marginTop: '6px' }}>
            ${overview?.platform_key_total_cost_usd?.toFixed(4) || '0.0000'}
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            Across {overview?.platform_key_total_calls || 0} platform API calls
          </span>
        </div>

        <div style={{
          background: 'rgba(24, 29, 40, 0.75)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '16px',
          padding: '20px'
        }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Total Workspaces
          </span>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#34d399', marginTop: '6px' }}>
            {overview?.total_workspaces || 0}
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            {overview?.total_users || 0} registered users
          </span>
        </div>

        <div style={{
          background: 'rgba(24, 29, 40, 0.75)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '16px',
          padding: '20px'
        }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Trial Kill-Switch Status
          </span>
          <div style={{
            fontSize: '1.25rem',
            fontWeight: 700,
            color: overview?.kill_switch_active ? '#ef4444' : '#34d399',
            marginTop: '10px'
          }}>
            {overview?.kill_switch_active ? 'TRIALS DISABLED' : 'TRIALS ACTIVE (3-CAP)'}
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            Env: DISABLE_PLATFORM_KEY_TRIALS
          </span>
        </div>
      </div>

      {/* Top Spenders & Workspaces Table */}
      <div style={{
        background: 'rgba(15, 20, 28, 0.85)',
        borderRadius: '20px',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        padding: '24px',
        marginBottom: '28px'
      }}>
        <h2 style={{ fontSize: '1.125rem', fontWeight: 700, margin: '0 0 16px 0', color: '#f8fafc' }}>
          Workspace Cost Breakdown & Top Spenders
        </h2>

        {(!usageData?.top_spenders || usageData.top_spenders.length === 0) ? (
          <div style={{ color: 'var(--text-muted)', fontSize: '0.875rem', padding: '16px 0' }}>
            No platform usage calls logged yet.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.08)', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '12px 16px' }}>Workspace</th>
                  <th style={{ padding: '12px 16px' }}>Type</th>
                  <th style={{ padding: '12px 16px' }}>Total Cost (USD)</th>
                  <th style={{ padding: '12px 16px' }}>Platform Calls</th>
                  <th style={{ padding: '12px 16px' }}>BYOK Calls</th>
                  <th style={{ padding: '12px 16px' }}>Controls</th>
                </tr>
              </thead>
              <tbody>
                {usageData.top_spenders.map((s: any) => (
                  <tr key={s.workspace_id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                    <td style={{ padding: '14px 16px', fontWeight: 600, color: '#f8fafc' }}>
                      {s.workspace_name}
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      {s.is_legacy ? (
                        <span style={{
                          background: 'rgba(245, 158, 11, 0.15)',
                          color: '#f59e0b',
                          padding: '3px 8px',
                          borderRadius: '6px',
                          fontSize: '0.75rem',
                          fontWeight: 700
                        }}>
                          Owner (Legacy)
                        </span>
                      ) : (
                        <span style={{
                          background: 'rgba(59, 130, 246, 0.15)',
                          color: '#60a5fa',
                          padding: '3px 8px',
                          borderRadius: '6px',
                          fontSize: '0.75rem',
                          fontWeight: 600
                        }}>
                          Tenant
                        </span>
                      )}
                    </td>
                    <td style={{ padding: '14px 16px', color: '#f59e0b', fontWeight: 700 }}>
                      ${s.total_cost_usd?.toFixed(4)}
                    </td>
                    <td style={{ padding: '14px 16px', color: 'var(--text-secondary)' }}>
                      {s.platform_calls}
                    </td>
                    <td style={{ padding: '14px 16px', color: '#34d399' }}>
                      {s.byok_calls}
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      {!s.is_legacy && (
                        <button
                          onClick={() => handleToggleWorkspace(s.workspace_id, true)}
                          disabled={actionLoading === s.workspace_id}
                          style={{
                            background: 'rgba(239, 68, 68, 0.15)',
                            border: '1px solid rgba(239, 68, 68, 0.3)',
                            color: '#ef4444',
                            borderRadius: '6px',
                            padding: '4px 8px',
                            fontSize: '0.75rem',
                            cursor: 'pointer'
                          }}
                        >
                          {actionLoading === s.workspace_id ? 'Updating...' : 'Pause Autopilot'}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Recent Ledger Records */}
      <div style={{
        background: 'rgba(15, 20, 28, 0.85)',
        borderRadius: '20px',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        padding: '24px'
      }}>
        <h2 style={{ fontSize: '1.125rem', fontWeight: 700, margin: '0 0 16px 0', color: '#f8fafc' }}>
          Recent Usage Ledger Audit Log
        </h2>

        {(!usageData?.recent_ledger_records || usageData.recent_ledger_records.length === 0) ? (
          <div style={{ color: 'var(--text-muted)', fontSize: '0.875rem', padding: '16px 0' }}>
            No recent records in usage ledger.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.8125rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.08)', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '10px 14px' }}>Timestamp</th>
                  <th style={{ padding: '10px 14px' }}>Provider</th>
                  <th style={{ padding: '10px 14px' }}>Operation</th>
                  <th style={{ padding: '10px 14px' }}>Units</th>
                  <th style={{ padding: '10px 14px' }}>Est. Cost</th>
                  <th style={{ padding: '10px 14px' }}>Billed To</th>
                </tr>
              </thead>
              <tbody>
                {usageData.recent_ledger_records.map((rec: any) => (
                  <tr key={rec.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.03)' }}>
                    <td style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>
                      {new Date(rec.timestamp).toLocaleString()}
                    </td>
                    <td style={{ padding: '10px 14px', fontWeight: 600, color: '#f8fafc' }}>
                      {rec.provider}
                    </td>
                    <td style={{ padding: '10px 14px', color: 'var(--text-secondary)' }}>
                      {rec.operation}
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      {rec.units} {rec.unit_type}
                    </td>
                    <td style={{ padding: '10px 14px', color: '#f59e0b' }}>
                      ${rec.estimated_cost_usd?.toFixed(5)}
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      {rec.used_platform_key ? (
                        <span style={{ color: '#ef4444', fontWeight: 600 }}>Platform Key (Trial)</span>
                      ) : (
                        <span style={{ color: '#34d399', fontWeight: 600 }}>Tenant BYOK</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
