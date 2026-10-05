import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  CheckCircle2,
  XCircle,
  Clock,
  User,
  Scale,
  FileText,
  AlertTriangle,
  ArrowRight,
  Sparkles,
} from 'lucide-react';
import { api } from '../lib/api';
import { GovernanceReceipt } from '../components/common/GovernanceReceipt';
import { DecisionBadge } from '../components/common/DecisionBadge';
import { HashChip } from '../components/common/HashChip';

export const ReviewsPage: React.FC = () => {
  const [pendingReviews, setPendingReviews] = useState<any[]>([]);
  const [selectedTicket, setSelectedTicket] = useState<any | null>(null);
  const [reviewNote, setReviewNote] = useState('');
  const [resolving, setResolving] = useState(false);
  const [resolutionSuccess, setResolutionSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchPending = async () => {
    try {
      const data = await api.getPendingReviews();
      setPendingReviews(data);
      if (data.length > 0 && !selectedTicket) {
        setSelectedTicket(data[0]);
      } else if (data.length === 0) {
        setSelectedTicket(null);
      }
    } catch (e) {
      console.error('Failed to load pending reviews', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPending();
  }, []);

  const handleResolve = async (resolution: 'APPROVE' | 'BLOCK') => {
    if (!selectedTicket || resolving) return;

    setResolving(true);
    setResolutionSuccess(null);

    const noteText = reviewNote.trim() || (resolution === 'APPROVE' ? 'Approved with manager exception authorization.' : 'Confirmed policy boundary violation.');

    try {
      const res = await api.resolveReview({
        action_id: selectedTicket.id,
        resolution: resolution === 'APPROVE' ? 'APPROVE_WITH_EXCEPTION' : 'REJECT_CONFIRMED',
        note: noteText,
      });

      setResolutionSuccess(
        `Ticket #${selectedTicket.id} successfully resolved: ${res.resolution}. Cryptographic resolution block #${res.resolution_entry_id} appended.`
      );
      setReviewNote('');

      // Refresh list
      const updatedList = pendingReviews.filter((t) => t.id !== selectedTicket.id);
      setPendingReviews(updatedList);
      setSelectedTicket(updatedList.length > 0 ? updatedList[0] : null);
    } catch (err: any) {
      alert(`Resolution failed: ${err.message}`);
    } finally {
      setResolving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-obsidian-900 to-obsidian-850 border border-border shadow-lg">
        <div>
          <h1 className="text-xl font-display font-bold text-white flex items-center gap-2">
            Human-in-the-Loop (HITL) Review Inbox
            <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
              {pendingReviews.length} Pending
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1 font-sans">
            Review compliance-flagged leave and expense requests requiring manager judgment or policy exception approval.
          </p>
        </div>
      </div>

      {resolutionSuccess && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-mono flex items-center gap-2 animate-fade-in shadow-emerald-glow">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{resolutionSuccess}</span>
        </div>
      )}

      {/* Split Review Viewport */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Tickets Queue */}
        <div className="lg:col-span-5 space-y-3">
          <h3 className="font-display font-semibold text-xs text-slate-400 uppercase tracking-wider px-1">
            Flagged Queue
          </h3>

          {loading ? (
            <div className="p-8 text-center text-xs font-mono text-slate-500 rounded-xl bg-obsidian-900 border border-border">
              Loading pending tickets...
            </div>
          ) : pendingReviews.length === 0 ? (
            <div className="p-12 text-center rounded-2xl bg-obsidian-900 border border-border space-y-3">
              <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto opacity-75" />
              <h4 className="font-display font-semibold text-sm text-slate-200">Review Queue Clear</h4>
              <p className="text-xs text-slate-400 max-w-xs mx-auto font-sans">
                All flagged actions have been reviewed and cryptographically sealed.
              </p>
            </div>
          ) : (
            pendingReviews.map((ticket) => (
              <div
                key={ticket.id}
                onClick={() => setSelectedTicket(ticket)}
                className={`p-4 rounded-xl border text-left cursor-pointer transition-all ${
                  selectedTicket?.id === ticket.id
                    ? 'bg-obsidian-850 border-sovereign-amber shadow-receipt'
                    : 'bg-obsidian-900 hover:bg-obsidian-850/80 border-border/80'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-sovereign-amber">#{ticket.id}</span>
                    <span className="font-display font-semibold text-xs text-slate-200">
                      {ticket.requester_name || ticket.employee_id}
                    </span>
                  </div>
                  <DecisionBadge decision={ticket.decision} size="sm" />
                </div>

                <p className="text-xs text-slate-300 mt-2 font-sans line-clamp-2 leading-relaxed">
                  {ticket.reason}
                </p>

                <div className="mt-3 pt-2 border-t border-border/60 flex items-center justify-between text-[11px] font-mono text-slate-500">
                  <span className="text-slate-400 truncate max-w-[180px]">{ticket.cited_rule}</span>
                  <span>{new Date(ticket.timestamp).toLocaleDateString()}</span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Right Column: Selected Ticket Inspection & Resolution Action */}
        <div className="lg:col-span-7 space-y-6">
          {selectedTicket ? (
            <div className="space-y-6 animate-fade-in">
              {/* Full Governance Receipt */}
              <GovernanceReceipt
                id={selectedTicket.id}
                timestamp={selectedTicket.timestamp}
                decision={selectedTicket.decision}
                reason={selectedTicket.reason}
                citedRule={selectedTicket.cited_rule}
                entryHash={selectedTicket.entry_hash}
                prevHash={selectedTicket.prev_hash}
                payload={selectedTicket.payload}
                requesterName={selectedTicket.requester_name}
                employeeId={selectedTicket.employee_id}
                reviewStatus={selectedTicket.review_status}
                actionType={selectedTicket.action_type}
              />

              {/* Manager Resolution Action Panel */}
              <div className="p-5 rounded-2xl bg-obsidian-900 border border-border space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-display font-semibold text-sm text-slate-200 flex items-center gap-2">
                    <Scale className="w-4 h-4 text-sovereign-amber" />
                    Manager Compliance Determination
                  </h3>
                  <span className="text-xs font-mono text-slate-500">Append-Only Resolution</span>
                </div>

                <div>
                  <label className="block text-xs font-mono text-slate-300 mb-1">
                    Justification Notes (Mandatory for Audit Trail)
                  </label>
                  <textarea
                    rows={3}
                    value={reviewNote}
                    onChange={(e) => setReviewNote(e.target.value)}
                    placeholder="Enter manager reason, medical cert verification, or business justification..."
                    className="w-full p-3 bg-obsidian-950 border border-border rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-sovereign-amber focus:border-sovereign-amber font-sans"
                  />
                </div>

                <div className="flex items-center gap-3 pt-2">
                  <button
                    onClick={() => handleResolve('APPROVE')}
                    disabled={resolving}
                    className="flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-obsidian-950 font-bold font-sans text-xs transition-all shadow-emerald-glow cursor-pointer disabled:opacity-50"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Approve with Exception</span>
                  </button>

                  <button
                    onClick={() => handleResolve('BLOCK')}
                    disabled={resolving}
                    className="flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-rose-500/15 hover:bg-rose-500/25 border border-rose-500/40 text-rose-300 font-bold font-sans text-xs transition-all shadow-rose-glow cursor-pointer disabled:opacity-50"
                  >
                    <XCircle className="w-4 h-4" />
                    <span>Confirm Policy Block</span>
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-12 text-center rounded-2xl bg-obsidian-900 border border-border text-slate-500 text-xs font-mono">
              Select a ticket from the left queue to inspect details and resolve.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
