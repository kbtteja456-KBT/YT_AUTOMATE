import React, { useState, useEffect } from 'react';
import { api, VaultResponse, VaultKeyInfo } from '../services/api';
import { KeyIcon, CheckCircleIcon, ExternalLinkIcon, SparklesIcon } from './Icons';

interface ApiKeyVaultModalProps {
  isOpen: boolean;
  onClose: () => void;
  onKeysUpdated?: () => void;
}

export const ApiKeyVaultModal: React.FC<ApiKeyVaultModalProps> = ({ isOpen, onClose, onKeysUpdated }) => {
  const [vaultData, setVaultData] = useState<VaultResponse | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<string>('openrouter');
  const [apiKeyInput, setApiKeyInput] = useState<string>('');
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadKeys();
    }
  }, [isOpen]);

  const loadKeys = async () => {
    try {
      const data = await api.getVaultKeys();
      setVaultData(data);
    } catch (e: any) {
      console.error('Failed to load keys:', e);
    }
  };

  const handleSaveKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKeyInput.trim()) return;

    setIsSaving(true);
    setMessage(null);
    try {
      const res = await api.saveVaultKey(selectedProvider, apiKeyInput.trim());
      setMessage({ type: 'success', text: res.message });
      setApiKeyInput('');
      await loadKeys();
      if (onKeysUpdated) onKeysUpdated();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Key verification failed' });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteKey = async (provider: string) => {
    if (!confirm(`Are you sure you want to remove your ${provider.toUpperCase()} key?`)) return;
    try {
      await api.deleteVaultKey(provider);
      await loadKeys();
      if (onKeysUpdated) onKeysUpdated();
    } catch (err: any) {
      alert(err.message || 'Failed to delete key');
    }
  };

  if (!isOpen) return null;

  const currentKey: VaultKeyInfo | undefined = vaultData?.configured_keys?.[selectedProvider];
  const guide = vaultData?.acquisition_guides?.[selectedProvider];

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(5, 7, 10, 0.85)',
      backdropFilter: 'blur(16px)',
      WebkitBackdropFilter: 'blur(16px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      padding: '20px'
    }}>
      <div style={{
        width: '100%',
        maxWidth: '620px',
        maxHeight: '90vh',
        overflowY: 'auto',
        background: 'rgba(15, 20, 28, 0.95)',
        border: '1px solid rgba(245, 158, 11, 0.3)',
        borderRadius: '24px',
        boxShadow: '0 24px 64px rgba(0, 0, 0, 0.85)',
        padding: '32px',
        position: 'relative'
      }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '42px',
              height: '42px',
              borderRadius: '12px',
              background: 'rgba(245, 158, 11, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#f59e0b'
            }}>
              <KeyIcon size={22} />
            </div>
            <div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, color: '#f8fafc' }}>
                API Key Vault (BYOK)
              </h2>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', margin: 0 }}>
                Encrypted at rest with AES-256. Raw keys are never sent to your browser.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)',
              fontSize: '1.5rem',
              cursor: 'pointer',
              lineHeight: 1
            }}
          >
            &times;
          </button>
        </div>

        {/* Provider Selector Tabs */}
        <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', overflowX: 'auto' }}>
          {[
            { id: 'openrouter', label: 'OpenRouter (LLM)' },
            { id: 'pexels', label: 'Pexels (Stock Video)' },
            { id: 'pixabay', label: 'Pixabay (Backup)' }
          ].map((tab) => {
            const hasKey = !!vaultData?.configured_keys?.[tab.id];
            const isSelected = selectedProvider === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => { setSelectedProvider(tab.id); setMessage(null); }}
                style={{
                  padding: '10px 16px',
                  borderRadius: '12px',
                  border: isSelected ? '1px solid rgba(245, 158, 11, 0.5)' : '1px solid rgba(255, 255, 255, 0.08)',
                  background: isSelected ? 'rgba(245, 158, 11, 0.15)' : 'rgba(24, 29, 40, 0.6)',
                  color: isSelected ? '#f59e0b' : 'var(--text-secondary)',
                  fontWeight: 600,
                  fontSize: '0.8125rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                {hasKey && <CheckCircleIcon size={14} color="#10b981" />}
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Current Key Status */}
        <div style={{
          background: 'rgba(9, 12, 16, 0.65)',
          borderRadius: '14px',
          padding: '16px',
          border: '1px solid rgba(255, 255, 255, 0.06)',
          marginBottom: '20px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Active Key Status
              </span>
              <div style={{ fontSize: '1rem', fontWeight: 600, marginTop: '4px', color: currentKey ? '#34d399' : '#94a3b8' }}>
                {currentKey ? (
                  <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <code>{currentKey.key_mask}</code> (Connected & Verified)
                  </span>
                ) : (
                  <span style={{ color: '#f59e0b' }}>Using Platform Free Trial Quota</span>
                )}
              </div>
            </div>
            {currentKey && (
              <button
                onClick={() => handleDeleteKey(selectedProvider)}
                style={{
                  background: 'rgba(239, 68, 68, 0.15)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  color: '#ef4444',
                  borderRadius: '8px',
                  padding: '6px 12px',
                  fontSize: '0.75rem',
                  cursor: 'pointer',
                  fontWeight: 600
                }}
              >
                Remove
              </button>
            )}
          </div>
        </div>

        {/* Feedback Alert */}
        {message && (
          <div style={{
            background: message.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
            border: `1px solid ${message.type === 'success' ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)'}`,
            color: message.type === 'success' ? '#34d399' : '#f87171',
            borderRadius: '10px',
            padding: '10px 14px',
            fontSize: '0.8125rem',
            marginBottom: '18px'
          }}>
            {message.text}
          </div>
        )}

        {/* Add / Update Key Input */}
        <form onSubmit={handleSaveKey} style={{ marginBottom: '24px' }}>
          <label style={{ display: 'block', fontSize: '0.8125rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
            {currentKey ? `Replace ${selectedProvider.toUpperCase()} Key` : `Add Your ${selectedProvider.toUpperCase()} Key`}
          </label>
          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              type="password"
              value={apiKeyInput}
              onChange={(e) => setApiKeyInput(e.target.value)}
              placeholder={`Paste your ${selectedProvider} API key...`}
              style={{
                flex: 1,
                padding: '12px 14px',
                background: 'rgba(24, 29, 40, 0.85)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                borderRadius: '12px',
                color: '#fff',
                fontSize: '0.9375rem',
                outline: 'none'
              }}
            />
            <button
              type="submit"
              disabled={isSaving || !apiKeyInput.trim()}
              style={{
                padding: '0 20px',
                background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
                border: 'none',
                borderRadius: '12px',
                color: '#000',
                fontWeight: 700,
                fontSize: '0.875rem',
                cursor: (isSaving || !apiKeyInput.trim()) ? 'not-allowed' : 'pointer',
                opacity: (isSaving || !apiKeyInput.trim()) ? 0.6 : 1
              }}
            >
              {isSaving ? 'Verifying...' : 'Save & Verify'}
            </button>
          </div>
        </form>

        {/* Step-by-Step Acquisition Guide Accordion */}
        {guide && (
          <div style={{
            background: 'rgba(24, 29, 40, 0.5)',
            borderRadius: '16px',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            padding: '18px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <SparklesIcon size={16} color="#f59e0b" />
                <span style={{ fontWeight: 600, fontSize: '0.875rem', color: '#f8fafc' }}>
                  How to get your free {guide.name} key
                </span>
              </div>
              <a
                href={guide.signup_url}
                target="_blank"
                rel="noreferrer"
                style={{
                  fontSize: '0.75rem',
                  color: '#f59e0b',
                  textDecoration: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  fontWeight: 600
                }}
              >
                Get Key Online <ExternalLinkIcon size={12} />
              </a>
            </div>

            <div style={{ fontSize: '0.75rem', color: '#10b981', fontWeight: 600, marginBottom: '10px' }}>
              Cost: {guide.cost}
            </div>

            <ol style={{ paddingLeft: '20px', color: 'var(--text-secondary)', fontSize: '0.8125rem', lineHeight: 1.6 }}>
              {guide.step_by_step.map((step, idx) => (
                <li key={idx} style={{ marginBottom: '4px' }}>{step}</li>
              ))}
            </ol>
          </div>
        )}
      </div>
    </div>
  );
};
