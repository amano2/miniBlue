import React, { useEffect, useState } from 'react';
import { ShieldCheck, Cpu, Zap, UserCheck, RefreshCw } from 'lucide-react';
import { useAuthStore } from '../../lib/store';
import { api } from '../../lib/api';
import { UserRole } from '../../types';

export const Header: React.FC = () => {
  const { user, login } = useAuthStore();
  const [healthStatus, setHealthStatus] = useState<{ status: string; index_status: string; llm_provider: string } | null>(null);
  const [isSwitching, setIsSwitching] = useState(false);

  useEffect(() => {
    api.getHealth()
      .then(setHealthStatus)
      .catch(() => setHealthStatus({ status: 'healthy', index_status: 'ready', llm_provider: 'gemini' }));
  }, []);

  const switchRole = async (targetRole: UserRole) => {
    setIsSwitching(true);
    const emails: Record<UserRole, string> = {
      employee: 'employee@miniblue.dev',
      manager: 'manager@miniblue.dev',
      admin: 'admin@miniblue.dev',
      auditor: 'auditor@miniblue.dev',
    };

    try {
      const tokens = await api.login(emails[targetRole], 'MiniBlue2026!');
      const profile = await api.getMe();
      login(tokens, profile);
    } catch (e) {
      console.error('Role switch failed', e);
    } finally {
      setIsSwitching(false);
    }
  };

  return (
    <header className="h-16 px-6 bg-obsidian-950/80 backdrop-blur-md border-b border-border flex items-center justify-between z-20">
      {/* Left: System Status & Architecture Title */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-mono text-xs">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>RightAction™ Governed</span>
        </div>

        <div className="hidden md:flex items-center gap-2 px-2.5 py-1 rounded-full bg-obsidian-900 border border-border text-slate-400 font-mono text-xs">
          <Cpu className="w-3.5 h-3.5 text-sovereign-ice" />
          <span>Multi-Agent Router (0-Cost Gemini)</span>
        </div>
      </div>

      {/* Right: Quick Demo Role Switcher & User Status */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1 bg-obsidian-900/90 p-1 rounded-lg border border-border text-xs">
          <span className="text-[11px] font-mono text-slate-500 px-2 flex items-center gap-1">
            <UserCheck className="w-3 h-3 text-sovereign-amber" />
            Switch:
          </span>
          {(['employee', 'manager', 'admin', 'auditor'] as UserRole[]).map((r) => (
            <button
              key={r}
              disabled={isSwitching || user?.role === r}
              onClick={() => switchRole(r)}
              className={`px-2 py-0.5 rounded text-[11px] font-mono capitalize transition-all cursor-pointer ${
                user?.role === r
                  ? 'bg-sovereign-amber text-obsidian-950 font-bold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-obsidian-800'
              }`}
            >
              {r}
            </button>
          ))}
        </div>
      </div>
    </header>
  );
};
