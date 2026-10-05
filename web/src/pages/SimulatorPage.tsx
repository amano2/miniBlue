import React, { useState } from 'react';
import {
  Sliders,
  Play,
  RotateCcw,
  ShieldCheck,
  AlertTriangle,
  ShieldAlert,
  ArrowRight,
  TrendingUp,
  Lock,
  History,
  CheckCircle2,
} from 'lucide-react';
import { api } from '../lib/api';
import { SimulationResult } from '../types';
import { HashChip } from '../components/common/HashChip';

const DEFAULT_PARAMS = {
  broadband_cap: 75,
  ergonomic_cap: 300,
  meal_cap: 30,
  hotel_cap: 200,
  sick_notice_threshold: 3,
};

export const SimulatorPage: React.FC = () => {
  const [params, setParams] = useState(DEFAULT_PARAMS);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRunSimulation = async () => {
    setRunning(true);
    setError(null);
    try {
      const res = await api.runSimulation(params);
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Simulation failed.');
    } finally {
      setRunning(false);
    }
  };

  const handleReset = () => {
    setParams(DEFAULT_PARAMS);
    setResult(null);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-obsidian-900 to-obsidian-850 border border-border shadow-lg">
        <div>
          <h1 className="text-xl font-display font-bold text-white flex items-center gap-2">
            Counterfactual Policy What-If Simulator
            <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
              Live Chain Isolated
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1 font-sans">
            Model the impact of prospective policy threshold adjustments against real historical claims before updating handbooks.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleReset}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-obsidian-950 hover:bg-obsidian-850 border border-border text-xs font-mono text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Caps</span>
          </button>

          <button
            onClick={handleRunSimulation}
            disabled={running}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-sovereign-amber to-amber-500 hover:from-amber-400 hover:to-amber-500 text-obsidian-950 font-bold font-sans text-xs shadow-amber-glow transition-all cursor-pointer disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>{running ? 'Simulating...' : 'Run Simulation'}</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-mono">
          {error}
        </div>
      )}

      {/* Grid: Sliders on Left, Results on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: 5 Parameter Sliders */}
        <div className="lg:col-span-5 p-5 rounded-2xl bg-obsidian-900 border border-border space-y-6">
          <div className="flex items-center justify-between border-b border-border/70 pb-3">
            <h3 className="font-display font-semibold text-sm text-slate-200 flex items-center gap-2">
              <Sliders className="w-4 h-4 text-sovereign-amber" />
              Adjust Policy Thresholds
            </h3>
            <span className="text-[11px] font-mono text-slate-500">5 Parameters</span>
          </div>

          {/* 1. Monthly Broadband Cap */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <label className="font-medium text-slate-300">Monthly Broadband Cap</label>
              <span className="font-mono text-sovereign-amber font-bold text-sm">${params.broadband_cap} / mo</span>
            </div>
            <input
              type="range"
              min={25}
              max={150}
              step={5}
              value={params.broadband_cap}
              onChange={(e) => setParams({ ...params, broadband_cap: Number(e.target.value) })}
              className="w-full accent-sovereign-amber cursor-pointer"
            />
            <div className="flex justify-between text-[10px] font-mono text-slate-500">
              <span>$25</span>
              <span>Baseline: $50</span>
              <span>$150</span>
            </div>
          </div>

          {/* 2. Ergonomic Equipment Cap */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <label className="font-medium text-slate-300">Ergonomic Equipment Annual Cap</label>
              <span className="font-mono text-sovereign-amber font-bold text-sm">${params.ergonomic_cap} / yr</span>
            </div>
            <input
              type="range"
              min={100}
              max={600}
              step={25}
              value={params.ergonomic_cap}
              onChange={(e) => setParams({ ...params, ergonomic_cap: Number(e.target.value) })}
              className="w-full accent-sovereign-amber cursor-pointer"
            />
            <div className="flex justify-between text-[10px] font-mono text-slate-500">
              <span>$100</span>
              <span>Baseline: $300</span>
              <span>$600</span>
            </div>
          </div>

          {/* 3. Meal Per Diem Cap */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <label className="font-medium text-slate-300">Daily Meal Per Diem</label>
              <span className="font-mono text-sovereign-amber font-bold text-sm">${params.meal_cap} / day</span>
            </div>
            <input
              type="range"
              min={15}
              max={100}
              step={5}
              value={params.meal_cap}
              onChange={(e) => setParams({ ...params, meal_cap: Number(e.target.value) })}
              className="w-full accent-sovereign-amber cursor-pointer"
            />
            <div className="flex justify-between text-[10px] font-mono text-slate-500">
              <span>$15</span>
              <span>Baseline: $30</span>
              <span>$100</span>
            </div>
          </div>

          {/* 4. Hotel Lodging Cap */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <label className="font-medium text-slate-300">Nightly Hotel Room Cap</label>
              <span className="font-mono text-sovereign-amber font-bold text-sm">${params.hotel_cap} / night</span>
            </div>
            <input
              type="range"
              min={100}
              max={400}
              step={10}
              value={params.hotel_cap}
              onChange={(e) => setParams({ ...params, hotel_cap: Number(e.target.value) })}
              className="w-full accent-sovereign-amber cursor-pointer"
            />
            <div className="flex justify-between text-[10px] font-mono text-slate-500">
              <span>$100</span>
              <span>Baseline: $200</span>
              <span>$400</span>
            </div>
          </div>

          {/* 5. Sick Leave Notice / Cert Threshold */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <label className="font-medium text-slate-300">Sick Leave Cert Threshold</label>
              <span className="font-mono text-sovereign-amber font-bold text-sm">{params.sick_notice_threshold} Days</span>
            </div>
            <input
              type="range"
              min={1}
              max={7}
              step={1}
              value={params.sick_notice_threshold}
              onChange={(e) => setParams({ ...params, sick_notice_threshold: Number(e.target.value) })}
              className="w-full accent-sovereign-amber cursor-pointer"
            />
            <div className="flex justify-between text-[10px] font-mono text-slate-500">
              <span>1 Day</span>
              <span>Baseline: 3 Days</span>
              <span>7 Days</span>
            </div>
          </div>
        </div>

        {/* Right Column: Simulation Impact Results */}
        <div className="lg:col-span-7 space-y-6">
          {result ? (
            <div className="space-y-6 animate-fade-in">
              {/* Chain Isolation Banner */}
              <div className="p-4 rounded-xl bg-obsidian-900 border border-emerald-500/30 flex items-center justify-between gap-3 text-xs font-mono">
                <div className="flex items-center gap-2 text-emerald-400">
                  <Lock className="w-4 h-4 shrink-0" />
                  <span>Immutable Chain Unaltered:</span>
                </div>
                <HashChip hash={result.chain_head_hash} truncateLength={10} />
              </div>

              {/* Before vs After Distribution Cards */}
              <div className="grid grid-cols-2 gap-4">
                {/* Baseline Card */}
                <div className="p-5 rounded-2xl bg-obsidian-900 border border-border space-y-3">
                  <span className="text-xs font-mono text-slate-500 uppercase">Baseline (Current Rules)</span>
                  <div className="space-y-2 text-xs font-mono">
                    <div className="flex justify-between text-emerald-400">
                      <span>Approved:</span>
                      <span className="font-bold">{result.before['APPROVE'] || 0}</span>
                    </div>
                    <div className="flex justify-between text-amber-400">
                      <span>Flagged:</span>
                      <span className="font-bold">{result.before['FLAG_FOR_REVIEW'] || 0}</span>
                    </div>
                    <div className="flex justify-between text-rose-400">
                      <span>Blocked:</span>
                      <span className="font-bold">{result.before['BLOCK'] || 0}</span>
                    </div>
                  </div>
                </div>

                {/* Simulated Card */}
                <div className="p-5 rounded-2xl bg-obsidian-900 border border-sovereign-amber/40 shadow-receipt space-y-3">
                  <span className="text-xs font-mono text-sovereign-amber uppercase font-semibold">Simulated Outcome</span>
                  <div className="space-y-2 text-xs font-mono">
                    <div className="flex justify-between text-emerald-400">
                      <span>Approved:</span>
                      <span className="font-bold">{result.after['APPROVE'] || 0}</span>
                    </div>
                    <div className="flex justify-between text-amber-400">
                      <span>Flagged:</span>
                      <span className="font-bold">{result.after['FLAG_FOR_REVIEW'] || 0}</span>
                    </div>
                    <div className="flex justify-between text-rose-400">
                      <span>Blocked:</span>
                      <span className="font-bold">{result.after['BLOCK'] || 0}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Shift Details Table */}
              <div className="p-5 rounded-2xl bg-obsidian-900 border border-border space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="font-display font-semibold text-sm text-slate-200 flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-sovereign-ice" />
                    Transaction Shift Analysis ({result.shifts.length} affected)
                  </h3>
                  <span className="text-xs font-mono text-slate-500">
                    Evaluated: {result.total_evaluated} records
                  </span>
                </div>

                {result.shifts.length === 0 ? (
                  <p className="text-xs font-mono text-slate-500 py-6 text-center">
                    No transactions shifted under these slider settings.
                  </p>
                ) : (
                  <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
                    {result.shifts.map((s, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-lg bg-obsidian-950 border border-border/80 flex items-center justify-between text-xs font-mono"
                      >
                        <div className="flex items-center gap-2.5">
                          <span className="text-sovereign-amber font-bold">#{s.action_id}</span>
                          <span className="text-slate-400 uppercase text-[10px]">{s.action_type || 'action'}</span>
                          <span className="text-slate-300 font-sans">{s.description || s.rule_applied}</span>
                        </div>

                        <div className="flex items-center gap-2 shrink-0">
                          <span className="text-slate-500">{s.original_decision}</span>
                          <ArrowRight className="w-3.5 h-3.5 text-sovereign-amber" />
                          <span className="text-sovereign-amber font-bold">{s.simulated_decision}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="p-16 text-center rounded-2xl bg-obsidian-900 border border-border text-slate-500 text-xs font-mono space-y-2">
              <Sliders className="w-8 h-8 text-slate-600 mx-auto" />
              <p>Adjust the sliders on the left and click "Run Simulation" to model compliance impact.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
