import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Lock, Mail, ArrowRight, CheckCircle2, ShieldAlert, Scale, Sparkles, Terminal } from 'lucide-react';
import { useAuthStore } from '../lib/store';
import { api } from '../lib/api';
import { GovernanceReceipt } from '../components/common/GovernanceReceipt';
import { UserRole } from '../types';

const DEMO_USERS: Array<{
  role: UserRole;
  title: string;
  name: string;
  email: string;
  badgeColor: string;
  description: string;
}> = [
  {
    role: 'employee',
    title: 'Employee Portal',
    name: 'Alex Mercer',
    email: 'employee@miniblue.dev',
    badgeColor: 'border-sky-500/30 text-sky-400 bg-sky-500/10',
    description: 'Submit leave, draft expense claims & ask policy questions',
  },
  {
    role: 'manager',
    title: 'Manager & HRBP',
    name: 'Sarah Chen',
    email: 'manager@miniblue.dev',
    badgeColor: 'border-amber-500/30 text-amber-400 bg-amber-500/10',
    description: 'Human-in-the-Loop review queue for compliance-flagged requests',
  },
  {
    role: 'admin',
    title: 'System Admin',
    name: 'David Vance',
    email: 'admin@miniblue.dev',
    badgeColor: 'border-emerald-500/30 text-emerald-400 bg-emerald-500/10',
    description: 'Policy what-if simulator, FAISS re-indexing, user administration',
  },
  {
    role: 'auditor',
    title: 'Compliance Auditor',
    name: 'Elena Rostova',
    email: 'auditor@miniblue.dev',
    badgeColor: 'border-purple-500/30 text-purple-400 bg-purple-500/10',
    description: 'Cryptographic SHA-256 chain verification & immutable CSV export',
  },
];

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('employee@miniblue.dev');
  const [password, setPassword] = useState('MiniBlue2026!');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { login } = useAuthStore();
  const navigate = useNavigate();

  const handleLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const tokens = await api.login(email.trim(), password);
      const profile = await api.getMe();
      login(tokens, profile);

      // Route based on role
      if (profile.role === 'employee') {
        navigate('/chat');
      } else if (profile.role === 'manager') {
        navigate('/reviews');
      } else {
        navigate('/dashboard');
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickDemo = (demoEmail: string) => {
    setEmail(demoEmail);
    setPassword('MiniBlue2026!');
  };

  return (
    <div className="min-h-screen bg-obsidian-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Background Decorative Mesh */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-sovereign-amber/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-sovereign-ice/5 rounded-full blur-3xl pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center z-10">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-amber-500/20 to-amber-600/10 border border-sovereign-amber/40 shadow-amber-glow text-sovereign-amber mb-4">
          <Shield className="w-8 h-8" />
        </div>
        <h2 className="text-3xl font-display font-extrabold text-white tracking-tight">
          miniBlue Platform
        </h2>
        <p className="mt-2 text-sm text-slate-400 font-sans">
          Enterprise Agentic HR Assistant & RightAction™ Compliance Engine
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-4xl z-10 px-4">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: Login Card & Demo Quick-Select */}
          <div className="lg:col-span-6 bg-obsidian-900/90 border border-border rounded-2xl p-6 shadow-2xl backdrop-blur-xl">
            <div className="mb-6">
              <span className="text-xs font-mono font-semibold tracking-wider text-sovereign-amber uppercase">
                1-Click Demo Personas
              </span>
              <p className="text-xs text-slate-400 mt-1">Select a role to test role-based permissions:</p>

              <div className="grid grid-cols-2 gap-2 mt-3">
                {DEMO_USERS.map((u) => (
                  <button
                    key={u.role}
                    type="button"
                    onClick={() => handleQuickDemo(u.email)}
                    className={`p-2.5 rounded-xl border text-left transition-all cursor-pointer ${
                      email === u.email
                        ? 'border-sovereign-amber bg-sovereign-amber/10 shadow-sm'
                        : 'border-border/80 bg-obsidian-950/70 hover:border-slate-600'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-display font-semibold text-xs text-slate-200">{u.name}</span>
                      <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded border ${u.badgeColor}`}>
                        {u.role}
                      </span>
                    </div>
                    <p className="text-[10px] text-slate-400 mt-1 truncate">{u.title}</p>
                  </button>
                ))}
              </div>
            </div>

            <form onSubmit={handleLogin} className="space-y-4">
              {error && (
                <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-mono">
                  {error}
                </div>
              )}

              <div>
                <label className="block text-xs font-mono font-medium text-slate-300">Corporate Email</label>
                <div className="mt-1 relative rounded-lg shadow-sm">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                    <Mail className="h-4 w-4" />
                  </div>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="block w-full pl-9 pr-3 py-2 text-xs bg-obsidian-950 border border-border rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-sovereign-amber focus:border-sovereign-amber font-mono"
                    placeholder="name@miniblue.dev"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-mono font-medium text-slate-300">Password</label>
                <div className="mt-1 relative rounded-lg shadow-sm">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                    <Lock className="h-4 w-4" />
                  </div>
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="block w-full pl-9 pr-3 py-2 text-xs bg-obsidian-950 border border-border rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-sovereign-amber focus:border-sovereign-amber font-mono"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full mt-2 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-gradient-to-r from-sovereign-amber to-amber-500 hover:from-amber-400 hover:to-amber-500 text-obsidian-950 font-bold font-sans text-xs shadow-amber-glow transition-all cursor-pointer disabled:opacity-50"
              >
                {loading ? 'Authenticating...' : 'Enter Sovereign HR Console'}
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          </div>

          {/* Right Column: Live RightAction Governance Architecture Showcase */}
          <div className="lg:col-span-6 space-y-4">
            <div className="p-4 rounded-2xl bg-obsidian-900/60 border border-border/80">
              <div className="flex items-center gap-2 text-xs font-mono text-sovereign-amber mb-2">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Zero Hallucination • Governed Actions</span>
              </div>
              <h3 className="text-sm font-display font-semibold text-slate-200">
                Auditable Boundary Control in Real Time
              </h3>
              <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                Specialist agents never execute actions silently. Every leave request and reimbursement claim passes
                through the deterministic RightAction layer and is sealed in a linear SHA-256 hash chain.
              </p>
            </div>

            {/* Live Interactive Receipt Preview */}
            <GovernanceReceipt
              id={42}
              timestamp={new Date().toISOString()}
              decision="FLAG_FOR_REVIEW"
              reason="Sick leave request for 4 consecutive days exceeds the 3-day self-certification limit. Routed to Manager Review Inbox for medical certificate verification."
              citedRule="HR-POL-001 §2.3 (Sick Leave Certification)"
              entryHash="7c4e918ab20d18fa34c679b3e10fa4876b341908d0112cfa812fbe9871ca2468"
              prevHash="3a1f8c7e90db6721ea5c4209fa8871b05c219807ab0134efa801bca961cd1254"
              payload={{
                leave_type: 'Sick Leave',
                days: 4.0,
                start_date: '2026-11-02',
                has_medical_certificate: false,
                notice_given: 'none',
              }}
              requesterName="Alex Mercer (Employee)"
              employeeId="EMP-001"
              reviewStatus="pending"
              actionType="leave"
            />
          </div>
        </div>
      </div>
    </div>
  );
};
