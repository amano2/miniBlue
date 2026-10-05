import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  Download,
  RefreshCw,
  CheckCircle2,
  AlertOctagon,
  Hash,
  Lock,
  ArrowDown,
  FileSpreadsheet,
} from 'lucide-react';
import { api } from '../lib/api';
import { AuditVerification, ActionLog } from '../types';
import { HashChip } from '../components/common/HashChip';
import { DecisionBadge } from '../components/common/DecisionBadge';

export const AuditPage: React.FC = () => {
  const [verification, setVerification] = useState<AuditVerification | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [actions, setActions] = useState<ActionLog[]>([]);
  const [loading, setLoading] = useState(true);

  const runVerification = async () => {
    setVerifying(true);
    try {
      const res = await api.verifyAuditChain();
      setVerification(res);
    } catch (e: any) {
      setVerification({
        valid: false,
        entries: 0,
        message: e.message || 'Chain verification failed.',
      });
    } finally {
      setVerifying(false);
    }
  };

  useEffect(() => {
    runVerification();
    api.getActions({ limit: 40 })
      .then(setActions)
      .catch((e) => console.error('Failed to load actions for audit ledger', e))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-obsidian-900 to-obsidian-850 border border-border shadow-lg">
        <div>
          <h1 className="text-xl font-display font-bold text-white flex items-center gap-2">
            Cryptographic Audit Ledger
            <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
              SHA-256 Chained
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1 font-sans">
            Mathematical proof of zero-tampering. Every RightAction compliance decision is immutably linked from genesis block #1.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={runVerification}
            disabled={verifying}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-obsidian-950 hover:bg-obsidian-850 border border-border hover:border-sovereign-amber/50 text-xs font-mono text-slate-300 hover:text-sovereign-amber transition-all cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${verifying ? 'animate-spin text-sovereign-amber' : ''}`} />
            <span>{verifying ? 'Verifying...' : 'Re-verify Chain'}</span>
          </button>

          <a
            href={api.getExportCsvUrl()}
            download
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-sovereign-amber hover:bg-amber-400 text-obsidian-950 font-bold font-sans text-xs shadow-amber-glow transition-all cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV Package</span>
          </a>
        </div>
      </div>

      {/* Verification Status Hero Banner */}
      {verification && (
        <div
          className={`p-5 rounded-2xl border flex flex-col md:flex-row md:items-center justify-between gap-4 transition-all ${
            verification.valid
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300 shadow-emerald-glow'
              : 'bg-rose-500/10 border-rose-500/30 text-rose-300 shadow-rose-glow'
          }`}
        >
          <div className="flex items-center gap-3.5">
            <div
              className={`w-12 h-12 rounded-xl border flex items-center justify-center shrink-0 ${
                verification.valid
                  ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-400'
                  : 'bg-rose-500/20 border-rose-500/40 text-rose-400'
              }`}
            >
              {verification.valid ? <ShieldCheck className="w-6 h-6" /> : <AlertOctagon className="w-6 h-6" />}
            </div>

            <div>
              <h3 className="font-display font-bold text-sm">
                {verification.valid ? 'Cryptographic Integrity 100% Verified' : 'Cryptographic Chain Integrity Breach'}
              </h3>
              <p className="text-xs font-mono opacity-90 mt-0.5">{verification.message}</p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 text-xs font-mono">
            <div className="px-3 py-1.5 rounded-lg bg-obsidian-950/70 border border-border">
              <span className="text-slate-500">Verified Blocks: </span>
              <span className="font-bold text-white">{verification.entries}</span>
            </div>

            {verification.head_hash && (
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-obsidian-950/70 border border-border">
                <span className="text-slate-500">Chain Head:</span>
                <HashChip hash={verification.head_hash} truncateLength={8} />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Linear Hash-Chained Blocks Viewer */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-display font-semibold text-sm text-slate-200">
            Immutable Block Ledger (Top 40 Blocks)
          </h3>
          <span className="text-xs font-mono text-slate-500">Genesis to Chain Head</span>
        </div>

        <div className="space-y-3">
          {loading ? (
            <div className="p-8 text-center text-xs font-mono text-slate-500 rounded-xl bg-obsidian-900 border border-border">
              Loading cryptographic blocks...
            </div>
          ) : (
            actions.map((block, idx) => (
              <div
                key={block.id}
                className="p-4 rounded-xl bg-obsidian-900 border border-border hover:border-border-active transition-all space-y-3"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2.5">
                    <span className="font-mono text-xs font-bold text-sovereign-amber bg-obsidian-950 px-2 py-0.5 rounded border border-border">
                      Block #{block.id}
                    </span>
                    <span className="font-display font-semibold text-xs text-slate-200">
                      {block.requester_name || block.employee_id}
                    </span>
                    <span className="font-mono text-[10px] text-slate-500 uppercase">
                      {block.action_type || block.entry_type}
                    </span>
                  </div>

                  <div className="flex items-center gap-3">
                    <DecisionBadge decision={block.decision} size="sm" />
                    <span className="font-mono text-[11px] text-slate-500">
                      {new Date(block.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-slate-300 font-sans leading-relaxed">
                  {block.reason}
                </p>

                {/* Hashes Row */}
                <div className="pt-2 border-t border-border/60 flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
                  <div className="flex items-center gap-2">
                    <span className="text-slate-500 text-[11px]">Prev:</span>
                    <HashChip hash={block.prev_hash} truncateLength={8} />
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-slate-500 text-[11px]">Entry SHA-256:</span>
                    <HashChip hash={block.entry_hash} truncateLength={10} />
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
