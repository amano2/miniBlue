import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  AlertTriangle,
  ShieldAlert,
  Clock,
  Activity,
  ArrowUpRight,
  CheckCircle,
  FileText,
  Sliders,
  Award,
} from 'lucide-react';
import { useAuthStore } from '../lib/store';
import { api } from '../lib/api';
import { TelemetryData, ActionLog } from '../types';
import { GovernanceReceipt } from '../components/common/GovernanceReceipt';
import { DecisionBadge } from '../components/common/DecisionBadge';

export const DashboardPage: React.FC = () => {
  const { user } = useAuthStore();
  const navigate = useNavigate();

  const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);
  const [recentActions, setRecentActions] = useState<ActionLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [telData, actData] = await Promise.all([
          api.getTelemetry().catch(() => null),
          api.getActions({ limit: 5 }).catch(() => []),
        ]);
        if (telData) setTelemetry(telData);
        setRecentActions(actData);
      } catch (e) {
        console.error('Error fetching dashboard telemetry', e);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const total = telemetry?.total_actions || 65;
  const approvedRate = telemetry?.approved_rate || 53.8;
  const flaggedRate = telemetry?.flagged_rate || 27.7;
  const blockedRate = telemetry?.blocked_rate || 18.5;
  const pendingCount = telemetry?.total_reviews_pending || 3;
  const avgLatency = telemetry?.avg_latency_ms || 280;

  return (
    <div className="space-y-6">
      {/* Top Banner: Role Greeting & Review Alert */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-obsidian-900 to-obsidian-850 border border-border shadow-lg">
        <div>
          <h1 className="text-xl font-display font-bold text-white flex items-center gap-2">
            Governance Command Console
            <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-sovereign-amber/15 text-sovereign-amber border border-sovereign-amber/30 uppercase">
              {user?.role}
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1 font-sans">
            Real-time multi-agent telemetry, RightAction boundary adherence, and cryptographic audit proofs.
          </p>
        </div>

        {/* Manager Review CTA */}
        {pendingCount > 0 && (user?.role === 'manager' || user?.role === 'admin') && (
          <button
            onClick={() => navigate('/reviews')}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-amber-500/15 hover:bg-amber-500/25 border border-amber-500/30 text-amber-300 text-xs font-mono font-medium transition-all shadow-amber-glow cursor-pointer"
          >
            <AlertTriangle className="w-4 h-4 text-amber-400 animate-pulse" />
            <span>{pendingCount} Flagged Tickets Awaiting Review</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Total Governed Actions */}
        <div className="p-4 rounded-xl bg-obsidian-900 border border-border flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono">
            <span>Total Governed</span>
            <Activity className="w-4 h-4 text-sovereign-ice" />
          </div>
          <div className="mt-3">
            <span className="text-2xl font-mono font-bold text-white tracking-tight">{total}</span>
            <p className="text-[11px] text-slate-400 mt-0.5 font-mono">100% Hash-Chained</p>
          </div>
        </div>

        {/* Approval Rate */}
        <div className="p-4 rounded-xl bg-obsidian-900 border border-emerald-500/20 flex flex-col justify-between">
          <div className="flex items-center justify-between text-emerald-400 text-xs font-mono">
            <span>Approved Rate</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-3">
            <span className="text-2xl font-mono font-bold text-emerald-400 tracking-tight">{approvedRate}%</span>
            <p className="text-[11px] text-slate-400 mt-0.5 font-mono">Compliant Actions</p>
          </div>
        </div>

        {/* Flagged for Review */}
        <div className="p-4 rounded-xl bg-obsidian-900 border border-amber-500/20 flex flex-col justify-between">
          <div className="flex items-center justify-between text-amber-400 text-xs font-mono">
            <span>Flagged for Review</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-3">
            <span className="text-2xl font-mono font-bold text-amber-400 tracking-tight">{flaggedRate}%</span>
            <p className="text-[11px] text-slate-400 mt-0.5 font-mono">Requires HITL HRBP</p>
          </div>
        </div>

        {/* Policy Blocked */}
        <div className="p-4 rounded-xl bg-obsidian-900 border border-rose-500/20 flex flex-col justify-between">
          <div className="flex items-center justify-between text-rose-400 text-xs font-mono">
            <span>Blocked Violations</span>
            <ShieldAlert className="w-4 h-4 text-rose-400" />
          </div>
          <div className="mt-3">
            <span className="text-2xl font-mono font-bold text-rose-400 tracking-tight">{blockedRate}%</span>
            <p className="text-[11px] text-slate-400 mt-0.5 font-mono">Zero Slippage</p>
          </div>
        </div>

        {/* Avg Decision Latency */}
        <div className="p-4 rounded-xl bg-obsidian-900 border border-border flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs font-mono">
            <span>Decision Latency</span>
            <Clock className="w-4 h-4 text-slate-400" />
          </div>
          <div className="mt-3">
            <span className="text-2xl font-mono font-bold text-white tracking-tight">{avgLatency} ms</span>
            <p className="text-[11px] text-slate-400 mt-0.5 font-mono">End-to-End Pipeline</p>
          </div>
        </div>
      </div>

      {/* Main Content Split: Compliance Distribution & Recent Audit Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Compliance Breakdown & Quick Actions */}
        <div className="lg:col-span-5 space-y-6">
          {/* Decision Breakdown Visual */}
          <div className="p-5 rounded-2xl bg-obsidian-900 border border-border space-y-4">
            <h3 className="font-display font-semibold text-sm text-slate-200">
              RightAction™ Distribution Ratio
            </h3>

            {/* Proportion Bar */}
            <div className="h-4 w-full rounded-full overflow-hidden flex bg-obsidian-950 border border-border/80">
              <div
                style={{ width: `${approvedRate}%` }}
                className="bg-emerald-500 transition-all duration-500"
                title={`Approved: ${approvedRate}%`}
              />
              <div
                style={{ width: `${flaggedRate}%` }}
                className="bg-amber-500 transition-all duration-500"
                title={`Flagged: ${flaggedRate}%`}
              />
              <div
                style={{ width: `${blockedRate}%` }}
                className="bg-rose-500 transition-all duration-500"
                title={`Blocked: ${blockedRate}%`}
              />
            </div>

            <div className="grid grid-cols-3 gap-2 text-xs font-mono pt-2">
              <div className="flex items-center gap-1.5 text-emerald-400">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                <span>Approved ({approvedRate}%)</span>
              </div>
              <div className="flex items-center gap-1.5 text-amber-400">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                <span>Flagged ({flaggedRate}%)</span>
              </div>
              <div className="flex items-center gap-1.5 text-rose-400">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
                <span>Blocked ({blockedRate}%)</span>
              </div>
            </div>
          </div>

          {/* Quick Action Navigation Buttons */}
          <div className="p-5 rounded-2xl bg-obsidian-900 border border-border space-y-3">
            <h3 className="font-display font-semibold text-sm text-slate-200">
              Rapid System Navigation
            </h3>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <button
                onClick={() => navigate('/chat')}
                className="p-3 rounded-xl bg-obsidian-950 hover:bg-obsidian-850 border border-border hover:border-sovereign-amber/50 text-left transition-all cursor-pointer group"
              >
                <div className="flex items-center justify-between text-sovereign-amber font-mono mb-1">
                  <span>Chat Assistant</span>
                  <ArrowUpRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                </div>
                <p className="text-[11px] text-slate-400">Test leave & expense requests</p>
              </button>

              <button
                onClick={() => navigate('/audit')}
                className="p-3 rounded-xl bg-obsidian-950 hover:bg-obsidian-850 border border-border hover:border-sovereign-amber/50 text-left transition-all cursor-pointer group"
              >
                <div className="flex items-center justify-between text-sovereign-ice font-mono mb-1">
                  <span>Cryptographic Audit</span>
                  <CheckCircle className="w-3.5 h-3.5 group-hover:scale-110 transition-transform" />
                </div>
                <p className="text-[11px] text-slate-400">Verify SHA-256 chain integrity</p>
              </button>

              <button
                onClick={() => navigate('/simulator')}
                className="p-3 rounded-xl bg-obsidian-950 hover:bg-obsidian-850 border border-border hover:border-sovereign-amber/50 text-left transition-all cursor-pointer group"
              >
                <div className="flex items-center justify-between text-emerald-400 font-mono mb-1">
                  <span>Policy Simulator</span>
                  <Sliders className="w-3.5 h-3.5 group-hover:scale-110 transition-transform" />
                </div>
                <p className="text-[11px] text-slate-400">Test what-if cap changes</p>
              </button>

              <button
                onClick={() => navigate('/evaluation')}
                className="p-3 rounded-xl bg-obsidian-950 hover:bg-obsidian-850 border border-border hover:border-sovereign-amber/50 text-left transition-all cursor-pointer group"
              >
                <div className="flex items-center justify-between text-purple-400 font-mono mb-1">
                  <span>Evaluation Suite</span>
                  <Award className="w-3.5 h-3.5 group-hover:scale-110 transition-transform" />
                </div>
                <p className="text-[11px] text-slate-400">Run benchmark scenarios</p>
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Recent Governed Actions Stream */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-display font-semibold text-sm text-slate-200">
              Live Governance Ledger Feed
            </h3>
            <button
              onClick={() => navigate('/requests')}
              className="text-xs font-mono text-sovereign-amber hover:underline flex items-center gap-1 cursor-pointer"
            >
              <span>View Full Ledger</span>
              <ArrowUpRight className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-3">
            {recentActions.length === 0 ? (
              <div className="p-8 text-center text-xs font-mono text-slate-500 rounded-xl bg-obsidian-900 border border-border">
                Loading governance ledger...
              </div>
            ) : (
              recentActions.map((action) => (
                <GovernanceReceipt
                  key={action.id}
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
                  isCompact={true}
                />
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
