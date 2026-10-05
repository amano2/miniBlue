import React, { useState, useEffect, useRef } from 'react';
import {
  Send,
  Plus,
  MessageSquare,
  Bot,
  User as UserIcon,
  Clock,
  Sparkles,
  BookOpen,
  Trash2,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { useAuthStore, useUIStore } from '../lib/store';
import { api } from '../lib/api';
import { ChatSession, ChatMessage } from '../types';
import { GovernanceReceipt } from '../components/common/GovernanceReceipt';

const SAMPLE_PROMPTS = [
  { label: 'Annual Leave (3 Days)', text: 'I want to apply for 3 days of annual leave starting next Monday with 2 weeks notice.' },
  { label: 'Sick Leave (>3 Days, No Cert)', text: 'I need 4 consecutive days of sick leave starting tomorrow. I do not have a doctor certificate yet.' },
  { label: 'Internet Claim ($45)', text: 'Please reimburse my home internet bill for $45 with invoice attached.' },
  { label: 'Hotel Claim ($320 Exceeds Cap)', text: 'Submitting a reimbursement claim for hotel stay in New York for $320 for 1 night as an Associate.' },
  { label: 'Notice Period Policy Question', text: 'What is the required notice period for annual leave according to company policy?' },
];

export const ChatPage: React.FC = () => {
  const { user } = useAuthStore();
  const { activeSessionId, setActiveSessionId } = useUIStore();

  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [openCitations, setOpenCitations] = useState<Record<string | number, boolean>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // Load user sessions
  useEffect(() => {
    api.getSessions()
      .then((data) => {
        setSessions(data);
        if (data.length > 0 && activeSessionId === 'default-session') {
          setActiveSessionId(data[0].session_id);
        }
      })
      .catch((e) => console.error('Failed to fetch sessions', e));
  }, []);

  // Load session transcript when activeSessionId changes
  useEffect(() => {
    if (!activeSessionId) return;

    api.getSessionTranscript(activeSessionId)
      .then((data) => {
        if (data.messages && data.messages.length > 0) {
          setMessages(data.messages);
        } else {
          // Default initial greeting
          setMessages([
            {
              id: 'init',
              timestamp: new Date().toISOString(),
              user_message: '',
              agent_used: 'Orchestrator Agent',
              intent: 'greeting',
              confidence: 1.0,
              reply: `Hello ${user?.full_name?.split(' ')[0] || 'there'}! I am your Enterprise HR Assistant.\n\nI can help you review official HR policies, submit governed leave applications, or process expense reimbursement claims with RightAction™ compliance guarantees.`,
              citations: [],
            },
          ]);
        }
      })
      .catch(() => {
        setMessages([
          {
            id: 'init',
            timestamp: new Date().toISOString(),
            user_message: '',
            agent_used: 'Orchestrator Agent',
            intent: 'greeting',
            confidence: 1.0,
            reply: `Hello ${user?.full_name?.split(' ')[0] || 'there'}! Ready to assist with HR policy questions or governed action requests.`,
            citations: [],
          },
        ]);
      });
  }, [activeSessionId, user]);

  const handleSendMessage = async (customMessage?: string) => {
    const textToSend = customMessage || inputText;
    if (!textToSend.trim() || loading) return;

    const userTurnText = textToSend.trim();
    setInputText('');
    setLoading(true);

    const tempUserMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      timestamp: new Date().toISOString(),
      user_message: userTurnText,
      agent_used: 'Orchestrator',
      intent: 'processing',
      confidence: 1.0,
      reply: '',
    };

    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const response = await api.sendMessage(userTurnText, activeSessionId);

      setMessages((prev) => {
        const filtered = prev.filter((m) => m.id !== tempUserMsg.id);
        return [
          ...filtered,
          {
            ...response,
            user_message: userTurnText,
          },
        ];
      });

      // Refresh sessions to show updated title
      api.getSessions().then(setSessions);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          timestamp: new Date().toISOString(),
          user_message: '',
          agent_used: 'System Fallback',
          intent: 'error',
          confidence: 0,
          reply: `⚠️ Request could not be processed: ${err.message || 'Server error'}. Please try again.`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleNewSession = () => {
    const newId = `session-${Date.now().toString(36)}`;
    setActiveSessionId(newId);
    setMessages([
      {
        id: `init-${newId}`,
        timestamp: new Date().toISOString(),
        user_message: '',
        agent_used: 'Orchestrator Agent',
        intent: 'greeting',
        confidence: 1.0,
        reply: `Started new HR consultation session #${newId}. How may I help you today?`,
      },
    ]);
  };

  const handleDeleteSession = async (sId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.deleteSession(sId);
      setSessions((prev) => prev.filter((s) => s.session_id !== sId));
      if (activeSessionId === sId) {
        handleNewSession();
      }
    } catch (err) {
      console.error('Failed to delete session', err);
    }
  };

  const toggleCitation = (msgId: string | number) => {
    setOpenCitations((prev) => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex rounded-2xl overflow-hidden border border-border bg-obsidian-950 shadow-2xl">
      {/* Left Drawer: Session List */}
      <div className="w-64 border-r border-border bg-obsidian-900/70 flex flex-col shrink-0">
        <div className="p-3 border-b border-border/80">
          <button
            onClick={handleNewSession}
            className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-xl bg-obsidian-850 hover:bg-obsidian-800 border border-sovereign-amber/30 text-sovereign-amber text-xs font-mono font-medium transition-all shadow-sm cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Chat Session</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {sessions.length === 0 ? (
            <p className="text-center text-[11px] font-mono text-slate-500 py-6">No previous sessions</p>
          ) : (
            sessions.map((s) => (
              <div
                key={s.session_id}
                onClick={() => setActiveSessionId(s.session_id)}
                className={`group flex items-center justify-between p-2.5 rounded-lg text-xs cursor-pointer transition-all ${
                  activeSessionId === s.session_id
                    ? 'bg-obsidian-800 text-sovereign-amber border border-sovereign-amber/30 font-medium'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-obsidian-850/60 border border-transparent'
                }`}
              >
                <div className="flex items-center gap-2 overflow-hidden">
                  <MessageSquare className="w-3.5 h-3.5 shrink-0" />
                  <span className="truncate text-[11px] font-sans">
                    {s.title || `Session ${s.session_id.slice(-6)}`}
                  </span>
                </div>
                <button
                  onClick={(e) => handleDeleteSession(s.session_id, e)}
                  className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-rose-400 p-1 transition-opacity cursor-pointer"
                  title="Delete session"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-obsidian-950">
        {/* Messages Stream */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.map((m, idx) => (
            <div key={m.id || idx} className="space-y-3">
              {/* User message echo */}
              {m.user_message && (
                <div className="flex justify-end items-start gap-2.5">
                  <div className="max-w-[75%] rounded-2xl rounded-tr-none px-4 py-3 bg-gradient-to-br from-amber-500/15 to-amber-600/10 border border-sovereign-amber/30 text-xs text-slate-100 font-sans shadow-md">
                    <p className="leading-relaxed whitespace-pre-wrap">{m.user_message}</p>
                    <span className="block text-[10px] font-mono text-sovereign-amber/70 mt-1 text-right">
                      {new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <div className="w-7 h-7 rounded-full bg-sovereign-amber/20 border border-sovereign-amber/40 flex items-center justify-center text-sovereign-amber text-[11px] font-mono shrink-0">
                    <UserIcon className="w-3.5 h-3.5" />
                  </div>
                </div>
              )}

              {/* Assistant response */}
              {m.reply && (
                <div className="flex justify-start items-start gap-2.5">
                  <div className="w-7 h-7 rounded-full bg-sky-500/15 border border-sky-500/30 flex items-center justify-center text-sovereign-ice text-[11px] font-mono shrink-0 mt-1">
                    <Bot className="w-3.5 h-3.5" />
                  </div>

                  <div className="max-w-[85%] space-y-3">
                    {/* Assistant bubble */}
                    <div className="rounded-2xl rounded-tl-none p-4 bg-obsidian-900 border border-border text-xs text-slate-200 font-sans shadow-lg space-y-2">
                      {/* Agent Attribution Pill & Latency */}
                      <div className="flex items-center justify-between pb-2 border-b border-border/60 text-[10px] font-mono">
                        <span className="flex items-center gap-1.5 text-sovereign-ice font-semibold">
                          <Sparkles className="w-3 h-3" />
                          {m.agent_used || 'Specialist Agent'}
                        </span>
                        {m.latency_ms !== undefined && (
                          <span className="text-slate-500 flex items-center gap-1">
                            <Clock className="w-2.5 h-2.5" />
                            {m.latency_ms} ms
                          </span>
                        )}
                      </div>

                      <div className="leading-relaxed whitespace-pre-wrap text-slate-200">
                        {m.reply}
                      </div>

                      {/* Citation Accordion */}
                      {m.citations && m.citations.length > 0 && (
                        <div className="pt-2 border-t border-border/40">
                          <button
                            onClick={() => toggleCitation(m.id)}
                            className="flex items-center gap-1.5 text-[11px] font-mono text-slate-400 hover:text-sovereign-amber transition-colors cursor-pointer"
                          >
                            <BookOpen className="w-3 h-3 text-sovereign-amber" />
                            <span>Grounded Policy Sources ({m.citations.length})</span>
                            {openCitations[m.id] ? (
                              <ChevronUp className="w-3 h-3 ml-1" />
                            ) : (
                              <ChevronDown className="w-3 h-3 ml-1" />
                            )}
                          </button>

                          {openCitations[m.id] && (
                            <div className="mt-2 space-y-1.5">
                              {m.citations.map((c, cIdx) => (
                                <div
                                  key={cIdx}
                                  className="p-2.5 rounded-lg bg-obsidian-950 border border-border/60 text-[11px] font-mono text-slate-300 space-y-1"
                                >
                                  <div className="flex items-center justify-between text-sovereign-amber text-[10px]">
                                    <span>{c.source_file || c.doc_id || 'Policy Document'}</span>
                                    {c.score !== undefined && (
                                      <span className="text-slate-500">RRF Score: {c.score}</span>
                                    )}
                                  </div>
                                  <p className="text-slate-400 font-sans text-xs italic">
                                    "{c.text}"
                                  </p>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Inline Governance Receipt Card */}
                    {(m.governance_decision || m.action) && (
                      <GovernanceReceipt
                        id={m.action_log_id || (m.action && m.action.id) || null}
                        timestamp={m.timestamp}
                        decision={m.governance_decision}
                        reason={m.reply}
                        citedRule={m.citations?.[0]?.source_file || 'HR Compliance Rule'}
                        entryHash={m.action_log_id ? `0x7a8f...${m.action_log_id}cf92` : undefined}
                        payload={m.action?.payload}
                        actionType={m.action?.type}
                      />
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex justify-start items-center gap-3 text-xs font-mono text-sovereign-amber animate-pulse p-4">
              <Bot className="w-4 h-4" />
              <span>Orchestrating agent retrieval & RightAction compliance gates...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Quick Suggestion Chips */}
        <div className="px-4 py-2 bg-obsidian-900/60 border-t border-border/60 flex items-center gap-2 overflow-x-auto">
          <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider shrink-0">
            Scenarios:
          </span>
          {SAMPLE_PROMPTS.map((p, i) => (
            <button
              key={i}
              onClick={() => handleSendMessage(p.text)}
              disabled={loading}
              className="px-2.5 py-1 rounded-full text-[11px] font-mono bg-obsidian-850 hover:bg-obsidian-800 border border-border text-slate-300 hover:text-sovereign-amber whitespace-nowrap transition-colors cursor-pointer disabled:opacity-50"
            >
              {p.label}
            </button>
          ))}
        </div>

        {/* Message Input Box */}
        <div className="p-4 bg-obsidian-900 border-t border-border">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center gap-3"
          >
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Ask a policy question or submit a leave / expense claim..."
              disabled={loading}
              className="flex-1 px-4 py-3 bg-obsidian-950 border border-border rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-sovereign-amber focus:border-sovereign-amber font-sans disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!inputText.trim() || loading}
              className="p-3 rounded-xl bg-sovereign-amber hover:bg-amber-400 text-obsidian-950 font-bold transition-all shadow-amber-glow cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
