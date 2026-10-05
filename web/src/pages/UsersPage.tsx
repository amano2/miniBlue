import React, { useState, useEffect } from 'react';
import { Users, UserPlus, Shield, CheckCircle, XCircle } from 'lucide-react';
import { User, UserRole } from '../types';

export const UsersPage: React.FC = () => {
  const [userList, setUserList] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);

  // Default demo personas
  useEffect(() => {
    setUserList([
      { id: 1, employee_id: 'EMP-001', email: 'employee@miniblue.dev', full_name: 'Alex Mercer', role: 'employee', department: 'Engineering', is_active: true },
      { id: 2, employee_id: 'MGR-002', email: 'manager@miniblue.dev', full_name: 'Sarah Chen', role: 'manager', department: 'People Operations', is_active: true },
      { id: 3, employee_id: 'ADM-003', email: 'admin@miniblue.dev', full_name: 'David Vance', role: 'admin', department: 'Human Resources', is_active: true },
      { id: 4, employee_id: 'AUD-004', email: 'auditor@miniblue.dev', full_name: 'Elena Rostova', role: 'auditor', department: 'Internal Audit', is_active: true },
    ]);
    setLoading(false);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-obsidian-900 to-obsidian-850 border border-border shadow-lg">
        <div>
          <h1 className="text-xl font-display font-bold text-white flex items-center gap-2">
            Enterprise RBAC User Management
            <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-sovereign-amber/15 text-sovereign-amber border border-sovereign-amber/30">
              {userList.length} Active Accounts
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1 font-sans">
            Assign and audit governance boundaries for Employees, Managers, Admins, and Compliance Auditors.
          </p>
        </div>
      </div>

      <div className="space-y-3">
        {userList.map((u) => (
          <div
            key={u.id}
            className="p-4 rounded-xl bg-obsidian-900 border border-border flex flex-wrap items-center justify-between gap-3 text-xs"
          >
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-sovereign-amber/15 border border-sovereign-amber/30 flex items-center justify-center font-mono font-bold text-sovereign-amber">
                {u.full_name[0]}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-display font-semibold text-slate-200">{u.full_name}</span>
                  <span className="font-mono text-[10px] text-slate-500">[{u.employee_id}]</span>
                </div>
                <p className="font-mono text-slate-400 text-[11px]">{u.email}</p>
              </div>
            </div>

            <div className="flex items-center gap-4 font-mono">
              <span className="text-slate-400">{u.department}</span>
              <span className="px-2.5 py-1 rounded-full uppercase text-[10px] font-bold bg-obsidian-950 text-sovereign-amber border border-sovereign-amber/30">
                {u.role}
              </span>
              <span className="text-emerald-400 flex items-center gap-1 text-[11px]">
                <CheckCircle className="w-3.5 h-3.5" />
                Active
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
