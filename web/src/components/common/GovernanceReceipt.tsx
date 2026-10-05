import React, { useState } from 'react';
import { ShieldCheck, ChevronDown, ChevronUp, Clock, Scale, User, FileText, ArrowRight } from 'lucide-react';
import { DecisionBadge } from './DecisionBadge';
import { HashChip } from './HashChip';
import { GovernanceDecision, ReviewStatus } from '../../types';

interface GovernanceReceiptProps {
  id?: number | string | null;
  timestamp?: string;
  decision?: GovernanceDecision | string | null;
  reason?: string;
  citedRule?: string;
  entryHash?: string;
  prevHash?: string;
  payload?: Record<string, any> | null;
  requesterName?: string | null;
  employeeId?: string | null;
  reviewStatus?: ReviewStatus | string;
  actionType?: string | null;
  isCompact?: boolean;
}

export const GovernanceReceipt: React.FC<GovernanceReceiptProps> = ({
  id,
  timestamp,
  decision = 'APPROVE',
  reason,
  citedRule,
  entryHash,
  prevHash,
  payload,
  requesterName,
  employeeId,
  reviewStatus = 'none',
  actionType,
  isCompact = false,
}) => {
  const [showPayload, setShowPayload] = useState(false);

  const formattedDate = timestamp
    ? new Date(timestamp).toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      })
    : new Date().toLocaleTimeString();

  return (
    <div className="governance-receipt rounded-xl overflow-hidden text-sm animate-fade-in border border-border shadow-receipt">
      {/* Receipt Top Ribbon */}
      <div className="px-4 py-2.5 bg-obsidian-950/70 border-b border-border/80 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 rounded bg-sovereign-amber/15 border border-sovereign-amber/30 flex items-center justify-center text-sovereign-amber">
            <ShieldCheck className="w-3.5 h-3.5" />
          </div>
          <span className="font-mono text-[11px] font-semibold tracking-wider text-slate-300 uppercase">
            RightAction™ Governance Receipt
          </span>
          {id && (
            <span className="font-mono text-[11px] px-1.5 py-0.5 rounded bg-obsidian-850 text-sovereign-amber border border-border">
              #{id}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {reviewStatus === 'pending' && (
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-amber-500/15 text-amber-300 border border-amber-500/30 animate-pulse">
              Pending HRBP Review
            </span>
          )}
          {reviewStatus === 'approved_exception' && (
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
              Resolved w/ Exception
            </span>
          )}
          <DecisionBadge decision={decision} size="sm" />
        </div>
      </div>

      {/* Main Receipt Body */}
      <div className="p-4 space-y-3.5">
        {/* Cited Rule & Policy Anchor */}
        {citedRule && (
          <div className="flex items-start gap-2 text-xs">
            <Scale className="w-4 h-4 text-sovereign-amber shrink-0 mt-0.5" />
            <div className="flex-1">
              <span className="text-slate-400 font-medium">Applied Boundary: </span>
              <span className="font-mono text-slate-200 bg-obsidian-950 px-2 py-0.5 rounded border border-border/70 text-[11px] font-semibold">
                {citedRule}
              </span>
            </div>
          </div>
        )}

        {/* Reason / Compliance Judgment */}
        {reason && (
          <div className="text-xs text-slate-300 bg-obsidian-950/60 p-3 rounded-lg border border-border/60 leading-relaxed font-sans">
            {reason}
          </div>
        )}

        {/* Structured Action Parameters */}
        {payload && Object.keys(payload).length > 0 && (
          <div className="border border-border/60 rounded-lg overflow-hidden bg-obsidian-950/40">
            <button
              onClick={() => setShowPayload(!showPayload)}
              className="w-full px-3 py-2 flex items-center justify-between text-xs text-slate-400 hover:text-slate-200 hover:bg-obsidian-900/60 transition-colors"
            >
              <span className="flex items-center gap-1.5 font-mono text-[11px]">
                <FileText className="w-3.5 h-3.5 text-sovereign-ice" />
                Parsed Action Parameters ({actionType || 'request'})
              </span>
              <span className="flex items-center gap-1 text-[11px] text-slate-500">
                {showPayload ? 'Collapse' : 'Inspect JSON'}
                {showPayload ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </span>
            </button>

            {showPayload && (
              <div className="p-3 border-t border-border/60 bg-obsidian-950/90 text-xs font-mono overflow-x-auto">
                <pre className="text-slate-300 text-[11px] leading-tight">
                  {JSON.stringify(payload, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}

        {/* Cryptographic Proof Block */}
        {!isCompact && entryHash && (
          <div className="pt-2 border-t border-border/60 space-y-1.5 font-mono text-[11px]">
            <div className="flex flex-wrap items-center justify-between gap-2 text-slate-400">
              <span className="text-slate-500">Block SHA-256:</span>
              <HashChip hash={entryHash} truncateLength={10} />
            </div>

            {prevHash && prevHash !== '0'.repeat(64) && (
              <div className="flex flex-wrap items-center justify-between gap-2 text-slate-500">
                <span>Prev Hash:</span>
                <HashChip hash={prevHash} truncateLength={8} />
              </div>
            )}
          </div>
        )}

        {/* Footer: Requester & UTC Timestamp */}
        <div className="pt-2 border-t border-border/40 flex items-center justify-between text-[11px] text-slate-500 font-mono">
          <div className="flex items-center gap-1.5">
            <Clock className="w-3 h-3 text-slate-600" />
            <span>{formattedDate}</span>
          </div>

          {(requesterName || employeeId) && (
            <div className="flex items-center gap-1.5">
              <User className="w-3 h-3 text-slate-600" />
              <span>{requesterName || employeeId}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
