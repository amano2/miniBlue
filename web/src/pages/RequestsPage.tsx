import React, { useState, useEffect } from 'react';
import {
  ClipboardList,
  Filter,
  Search,
  ChevronDown,
  ChevronUp,
  FileText,
  Clock,
  ExternalLink,
} from 'lucide-react';
import { api } from '../lib/api';
import { ActionLog } from '../types';
import { GovernanceReceipt } from '../components/common/GovernanceReceipt';
import { DecisionBadge } from '../components/common/DecisionBadge';
import { HashChip } from '../components/common/HashChip';

export const RequestsPage: React.FC = () => {
  const [actions, setActions] = useState<ActionLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [decisionFilter, setDecisionFilter] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedId, setExpandedId] = useState<number | null>(null);

  useEffect(() => {
    setLoading(true);
    api.getActions({
      decision: decisionFilter || undefined,
      action_type: typeFilter || undefined,
      limit: 100,
    })
      .then(setActions)
      .catch((e) => console.error('Failed to load actions', e))
      .finally(() => setLoading(false));
  }, [decisionFilter, typeFilter]);

  const filtered = actions.filter((a) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      (a.requester_name || '').toLowerCase().includes(q) ||
      (a.reason || '').toLowerCase().includes(q) ||
      (a.cited_rule || '').toLowerCase().includes(q) ||
      String(a.id).includes(q)
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-obsidian-900 to-obsidian-850 border border-border shadow-lg">
        <div>
          <h1 className="text-xl font-display font-bold text-white flex items-center gap-2">
            Governed Action Ledger
            <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-sovereign-amber/15 text-sovereign-amber border border-sovereign-amber/30">
              {filtered.length} Records
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1 font-sans">
            Immutable log of all employee leave applications, reimbursement claims, and RightAction compliance decisions.
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-xl bg-obsidian-900 border border-border flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-1 min-w-[240px]">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by ID, requester, or policy rule..."
              className="w-full pl-9 pr-3 py-2 bg-obsidian-950 border border-border rounded-lg text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-sovereign-amber focus:border-sovereign-amber font-mono"
            />
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Decision Filter */}
          <select
            value={decisionFilter}
            onChange={(e) => setDecisionFilter(e.target.value)}
            className="px-3 py-2 bg-obsidian-950 border border-border rounded-lg text-xs font-mono text-slate-300 focus:outline-none focus:border-sovereign-amber cursor-pointer"
          >
            <option value="">All Decisions</option>
            <option value="APPROVE">Approved</option>
            <option value="FLAG_FOR_REVIEW">Flagged</option>
            <option value="BLOCK">Blocked</option>
            <option value="APPROVE_WITH_EXCEPTION">Approved w/ Exception</option>
          </select>

          {/* Action Type Filter */}
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-3 py-2 bg-obsidian-950 border border-border rounded-lg text-xs font-mono text-slate-300 focus:outline-none focus:border-sovereign-amber cursor-pointer"
          >
            <option value="">All Action Types</option>
            <option value="leave">Leave Request</option>
            <option value="reimbursement">Reimbursement</option>
          </select>
        </div>
      </div>

      {/* Records Table */}
      <div className="space-y-3">
        {loading ? (
          <div className="p-8 text-center text-xs font-mono text-slate-500 rounded-xl bg-obsidian-900 border border-border">
            Loading actions from hash chain...
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center rounded-2xl bg-obsidian-900 border border-border text-slate-500 text-xs font-mono">
            No matching action records found.
          </div>
        ) : (
          filtered.map((action) => {
            const isExpanded = expandedId === action.id;
            return (
              <div
                key={action.id}
                className="rounded-xl border border-border bg-obsidian-900 overflow-hidden transition-all shadow-sm"
              >
                {/* Summary Row */}
                <div
                  onClick={() => setExpandedId(isExpanded ? null : action.id)}
                  className="p-4 flex items-center justify-between gap-4 cursor-pointer hover:bg-obsidian-850/60 transition-colors"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <span className="font-mono text-xs font-bold text-sovereign-amber shrink-0">
                      #{action.id}
                    </span>

                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-display font-semibold text-xs text-slate-200">
                          {action.requester_name || action.employee_id}
                        </span>
                        <span className="text-[10px] font-mono text-slate-500 uppercase px-1.5 py-0.2 rounded bg-obsidian-950 border border-border">
                          {action.action_type || 'action'}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 truncate mt-0.5 max-w-xl font-sans">
                        {action.reason}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 shrink-0">
                    <DecisionBadge decision={action.decision} size="sm" />
                    <span className="hidden sm:inline-block font-mono text-[11px] text-slate-500">
                      {new Date(action.timestamp).toLocaleDateString()}
                    </span>
                    {isExpanded ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                  </div>
                </div>

                {/* Expanded Full Governance Receipt */}
                {isExpanded && (
                  <div className="p-4 pt-0 border-t border-border/60 bg-obsidian-950/60">
                    <GovernanceReceipt
                      id={action.id}
                      timestamp={action.timestamp}
                      decision={action.decision}
                      reason={action.reason}
                      citedRule={action.cited_rule}
                      entryHash={action.entry_hash}
                      prevHash={action.prev_hash}
                      payload={action.payload}
                      requesterName={action.requester_name}
                      employeeId={action.employee_id}
                      reviewStatus={action.review_status}
                      actionType={action.action_type}
                    />
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
