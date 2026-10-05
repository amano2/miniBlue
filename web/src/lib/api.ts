import { useAuthStore } from './store';
import {
  AuthTokens,
  User,
  ActionLog,
  ChatSession,
  ChatMessage,
  TelemetryData,
  AuditVerification,
  PolicyDoc,
  SimulationResult,
  EvalRun,
} from '../types';

const API_BASE = '/api/v1';

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const tokens = useAuthStore.getState().tokens;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (tokens?.access_token) {
    headers['Authorization'] = `Bearer ${tokens.access_token}`;
  }

  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
  let res = await fetch(url, { ...options, headers });

  // Handle Token Expiry & Automatic Refresh
  if (res.status === 401 && tokens?.refresh_token) {
    try {
      const refreshRes = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: tokens.refresh_token }),
      });

      if (refreshRes.ok) {
        const newTokens: AuthTokens = await refreshRes.json();
        const currentUser = useAuthStore.getState().user;
        if (currentUser) {
          useAuthStore.getState().login(newTokens, currentUser);
        }
        headers['Authorization'] = `Bearer ${newTokens.access_token}`;
        res = await fetch(url, { ...options, headers });
      } else {
        useAuthStore.getState().logout();
      }
    } catch (e) {
      useAuthStore.getState().logout();
    }
  }

  if (!res.ok) {
    let errorDetail = 'API request failed';
    try {
      const errJson = await res.json();
      errorDetail = errJson.detail?.error?.message || errJson.detail?.message || errJson.detail || res.statusText;
    } catch {
      errorDetail = `${res.status} ${res.statusText}`;
    }
    throw new Error(errorDetail);
  }

  return res.json();
}

export const api = {
  // Auth
  login: async (email: string, password: string): Promise<AuthTokens> => {
    return request<AuthTokens>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  },
  getMe: async (): Promise<User> => {
    return request<User>('/auth/me');
  },

  // Chat
  sendMessage: async (message: string, session_id: string): Promise<ChatMessage> => {
    return request<ChatMessage>('/chat', {
      method: 'POST',
      body: JSON.stringify({ message, session_id }),
    });
  },
  getSessions: async (): Promise<ChatSession[]> => {
    return request<ChatSession[]>('/chat/sessions');
  },
  getSessionTranscript: async (sessionId: string): Promise<{ session_id: string; title: string; messages: any[] }> => {
    return request(`/chat/sessions/${sessionId}`);
  },
  deleteSession: async (sessionId: string): Promise<{ deleted: boolean }> => {
    return request(`/chat/sessions/${sessionId}`, { method: 'DELETE' });
  },

  // Actions
  getActions: async (params?: { decision?: string; action_type?: string; limit?: number }): Promise<ActionLog[]> => {
    const query = new URLSearchParams();
    if (params?.decision) query.set('decision', params.decision);
    if (params?.action_type) query.set('action_type', params.action_type);
    if (params?.limit) query.set('limit', String(params.limit));
    const qs = query.toString() ? `?${query.toString()}` : '';
    return request<ActionLog[]>(`/actions${qs}`);
  },
  getActionDetail: async (id: number): Promise<{ action: ActionLog; review_events: any[] }> => {
    return request(`/actions/${id}`);
  },

  // HITL Reviews
  getPendingReviews: async (): Promise<any[]> => {
    return request<any[]>('/reviews/pending');
  },
  resolveReview: async (payload: { action_id: number; resolution: string; note: string }): Promise<any> => {
    return request('/reviews/resolve', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // Simulator
  runSimulation: async (params: {
    broadband_cap: number;
    ergonomic_cap: number;
    meal_cap: number;
    hotel_cap: number;
    sick_notice_threshold: number;
  }): Promise<SimulationResult> => {
    return request<SimulationResult>('/simulate', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  },
  getSimulationRuns: async (): Promise<any[]> => {
    return request('/simulate/runs');
  },

  // Audit
  verifyAuditChain: async (): Promise<AuditVerification> => {
    return request<AuditVerification>('/audit/verify');
  },
  getExportCsvUrl: (): string => {
    return `${API_BASE}/audit/export.csv`;
  },

  // Telemetry
  getTelemetry: async (): Promise<TelemetryData> => {
    return request<TelemetryData>('/telemetry');
  },

  // Policies
  getPolicies: async (): Promise<PolicyDoc[]> => {
    return request<PolicyDoc[]>('/policies');
  },
  getPolicyDetail: async (docId: string): Promise<PolicyDoc & { chunks: any[] }> => {
    return request(`/policies/${docId}`);
  },
  reingestPolicies: async (): Promise<{ success: boolean; chunks_indexed: number; message: string }> => {
    return request('/policies/reingest', { method: 'POST' });
  },

  // Evaluation
  runEvaluation: async (): Promise<EvalRun> => {
    return request<EvalRun>('/eval/run', { method: 'POST' });
  },
  getEvalRuns: async (): Promise<any[]> => {
    return request('/eval/runs');
  },

  // Health
  getHealth: async (): Promise<{ status: string; index_status: string; llm_provider: string }> => {
    const res = await fetch('/health');
    return res.json();
  },
};
