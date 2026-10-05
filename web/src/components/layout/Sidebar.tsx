import React from 'react';
import { NavLink as RouterLink, useNavigate as useRouterNavigate } from 'react-router-dom';
import {
  MessageSquare,
  ClipboardList,
  ShieldAlert,
  Sliders,
  CheckCircle,
  FileText,
  BarChart3,
  Award,
  Users,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Shield,
} from 'lucide-react';
import { useAuthStore, useUIStore } from '../../lib/store';
import { UserRole } from '../../types';

interface NavItem {
  name: string;
  path: string;
  icon: React.ElementType;
  roles: UserRole[];
  badge?: string;
}

const NAV_ITEMS: NavItem[] = [
  { name: 'Chat Assistant', path: '/chat', icon: MessageSquare, roles: ['employee', 'manager', 'admin', 'auditor'] },
  { name: 'My Requests', path: '/requests', icon: ClipboardList, roles: ['employee', 'manager', 'admin', 'auditor'] },
  { name: 'Observability', path: '/dashboard', icon: BarChart3, roles: ['manager', 'admin', 'auditor'] },
  { name: 'Review Inbox', path: '/reviews', icon: ShieldAlert, roles: ['manager', 'admin'], badge: 'HITL' },
  { name: 'Policy Simulator', path: '/simulator', icon: Sliders, roles: ['admin'] },
  { name: 'Cryptographic Audit', path: '/audit', icon: CheckCircle, roles: ['admin', 'auditor'] },
  { name: 'Policy Library', path: '/policies', icon: FileText, roles: ['employee', 'manager', 'admin', 'auditor'] },
  { name: 'Compliance Eval', path: '/evaluation', icon: Award, roles: ['admin', 'auditor'] },
  { name: 'User Management', path: '/users', icon: Users, roles: ['admin'] },
];

export const Sidebar: React.FC = () => {
  const { user, logout } = useAuthStore();
  const { sidebarCollapsed, toggleSidebar } = useUIStore();
  const navigate = useRouterNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const userRole = (user?.role || 'employee') as UserRole;
  const filteredNav = NAV_ITEMS.filter((item) => item.roles.includes(userRole));

  return (
    <aside
      className={`relative flex flex-col bg-obsidian-950/95 border-r border-border transition-all duration-300 z-30 select-none ${
        sidebarCollapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-border/70 bg-obsidian-900/40">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-amber-500/20 to-amber-600/10 border border-sovereign-amber/40 flex items-center justify-center text-sovereign-amber shadow-amber-glow shrink-0">
            <Shield className="w-5 h-5" />
          </div>
          {!sidebarCollapsed && (
            <div className="flex flex-col">
              <span className="font-display font-bold text-base tracking-tight text-white flex items-center gap-1.5">
                miniBlue <span className="text-[10px] font-mono px-1 py-0.2 rounded bg-sovereign-amber/20 text-sovereign-amber border border-sovereign-amber/30">v3.0</span>
              </span>
              <span className="font-mono text-[10px] text-slate-400 tracking-wider uppercase">
                RightAction™ Engine
              </span>
            </div>
          )}
        </div>

        <button
          onClick={toggleSidebar}
          className="p-1.5 rounded-md text-slate-500 hover:text-slate-200 hover:bg-obsidian-800 transition-colors cursor-pointer"
          title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {sidebarCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation Items */}
      <div className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
        {filteredNav.map((item) => {
          const Icon = item.icon;
          return (
            <RouterLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `relative flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all group ${
                  isActive
                    ? 'bg-obsidian-800 text-sovereign-amber font-semibold border border-sovereign-amber/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-obsidian-900/80 border border-transparent'
                }`
              }
              title={sidebarCollapsed ? item.name : undefined}
            >
              <Icon className="w-4 h-4 shrink-0 transition-transform group-hover:scale-110" />

              {!sidebarCollapsed && (
                <div className="flex-1 flex items-center justify-between overflow-hidden">
                  <span className="truncate">{item.name}</span>
                  {item.badge && (
                    <span className="font-mono text-[9px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                      {item.badge}
                    </span>
                  )}
                </div>
              )}
            </RouterLink>
          );
        })}
      </div>

      {/* User Footer Profile & Role */}
      <div className="p-3 border-t border-border/70 bg-obsidian-900/60">
        <div className="flex items-center gap-2.5 overflow-hidden">
          <div className="w-8 h-8 rounded-full bg-sovereign-amber/15 border border-sovereign-amber/30 flex items-center justify-center text-xs font-mono font-bold text-sovereign-amber shrink-0">
            {user?.full_name ? user.full_name[0].toUpperCase() : 'U'}
          </div>

          {!sidebarCollapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-slate-200 truncate">{user?.full_name || 'Guest User'}</p>
              <div className="flex items-center gap-1.5">
                <span className="font-mono text-[10px] capitalize text-sovereign-amber font-semibold">
                  {user?.role}
                </span>
                <span className="text-[10px] text-slate-500">•</span>
                <span className="font-mono text-[10px] text-slate-400 truncate">
                  {user?.employee_id || 'ID'}
                </span>
              </div>
            </div>
          )}

          <button
            onClick={handleLogout}
            className="p-1.5 rounded text-slate-500 hover:text-rose-400 hover:bg-obsidian-800 transition-colors ml-auto cursor-pointer"
            title="Sign out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
};
