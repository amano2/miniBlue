import React, { useState, useEffect } from 'react';
import {
  FileText,
  BookOpen,
  RefreshCw,
  Layers,
  CheckCircle2,
  Download,
  Search,
} from 'lucide-react';
import { api } from '../lib/api';
import { PolicyDoc, PolicyChunk } from '../types';
import { useAuthStore } from '../lib/store';

export const PoliciesPage: React.FC = () => {
  const { user } = useAuthStore();
  const [policies, setPolicies] = useState<PolicyDoc[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>('HR-POL-001');
  const [selectedDoc, setSelectedDoc] = useState<(PolicyDoc & { chunks: PolicyChunk[] }) | null>(null);
  const [reingesting, setReingesting] = useState(false);
  const [reingestMsg, setReingestMsg] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'content' | 'chunks'>('content');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getPolicies()
      .then((data) => {
        setPolicies(data);
        if (data.length > 0) {
          setSelectedDocId(data[0].doc_id);
        }
      })
      .catch((e) => console.error('Failed to load policies', e))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedDocId) return;

    api.getPolicyDetail(selectedDocId)
      .then(setSelectedDoc)
      .catch((e) => console.error('Failed to load policy detail', e));
  }, [selectedDocId]);

  const handleReingest = async () => {
    setReingesting(true);
    setReingestMsg(null);
    try {
      const res = await api.reingestPolicies();
      setReingestMsg(res.message);
      // Refresh
      const updated = await api.getPolicies();
      setPolicies(updated);
    } catch (e: any) {
      alert(`Re-ingestion failed: ${e.message}`);
    } finally {
      setReingesting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-obsidian-900 to-obsidian-850 border border-border shadow-lg">
        <div>
          <h1 className="text-xl font-display font-bold text-white flex items-center gap-2">
            Corporate HR Policy Knowledge Fabric
            <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-sovereign-amber/15 text-sovereign-amber border border-sovereign-amber/30">
              {policies.length} Registered Policies
            </span>
          </h1>
          <p className="text-xs text-slate-400 mt-1 font-sans">
            Official policy handbooks chunked and indexed into local FAISS + BM25 hybrid vector store.
          </p>
        </div>

        {user?.role === 'admin' && (
          <button
            onClick={handleReingest}
            disabled={reingesting}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-sovereign-amber hover:bg-amber-400 text-obsidian-950 font-bold font-sans text-xs shadow-amber-glow transition-all cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${reingesting ? 'animate-spin' : ''}`} />
            <span>{reingesting ? 'Re-indexing Vector Store...' : 'Re-index FAISS & BM25'}</span>
          </button>
        )}
      </div>

      {reingestMsg && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-mono flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{reingestMsg}</span>
        </div>
      )}

      {/* Grid: Policy Tabs & Document Viewer */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Document Cards Selector */}
        <div className="lg:col-span-4 space-y-2">
          {policies.map((doc) => (
            <button
              key={doc.doc_id}
              onClick={() => setSelectedDocId(doc.doc_id)}
              className={`w-full p-4 rounded-xl border text-left transition-all cursor-pointer ${
                selectedDocId === doc.doc_id
                  ? 'bg-obsidian-850 border-sovereign-amber shadow-receipt'
                  : 'bg-obsidian-900 hover:bg-obsidian-850/80 border-border/80'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-sovereign-amber">{doc.doc_id}</span>
                <span className="text-[10px] font-mono text-slate-500">v{doc.version}</span>
              </div>
              <h3 className="font-display font-semibold text-xs text-slate-200 mt-1">{doc.title}</h3>
              <div className="mt-2 pt-2 border-t border-border/60 flex items-center justify-between text-[11px] font-mono text-slate-500">
                <span>{doc.filename}</span>
                <span className="text-sovereign-ice">{doc.chunk_count} Chunks</span>
              </div>
            </button>
          ))}
        </div>

        {/* Right Column: Full Document Reader & Chunks Inspection */}
        <div className="lg:col-span-8 p-6 rounded-2xl bg-obsidian-900 border border-border space-y-4">
          {selectedDoc ? (
            <div>
              {/* Document Header & Tabs */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-border/80">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-sovereign-amber bg-obsidian-950 px-2 py-0.5 rounded border border-border">
                      {selectedDoc.doc_id}
                    </span>
                    <h2 className="font-display font-bold text-base text-white">{selectedDoc.title}</h2>
                  </div>
                  <p className="text-xs font-mono text-slate-500 mt-1">Source: {selectedDoc.filename}</p>
                </div>

                {/* Content / Chunks Toggle */}
                <div className="flex items-center gap-1 bg-obsidian-950 p-1 rounded-lg border border-border text-xs font-mono">
                  <button
                    onClick={() => setActiveTab('content')}
                    className={`px-3 py-1 rounded transition-colors cursor-pointer ${
                      activeTab === 'content'
                        ? 'bg-sovereign-amber text-obsidian-950 font-bold'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    Policy Text
                  </button>
                  <button
                    onClick={() => setActiveTab('chunks')}
                    className={`px-3 py-1 rounded transition-colors cursor-pointer ${
                      activeTab === 'chunks'
                        ? 'bg-sovereign-amber text-obsidian-950 font-bold'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    RAG Chunks ({selectedDoc.chunks?.length || 0})
                  </button>
                </div>
              </div>

              {/* Viewport */}
              <div className="pt-4 max-h-[600px] overflow-y-auto pr-2">
                {activeTab === 'content' ? (
                  <div className="text-xs text-slate-300 leading-relaxed font-sans whitespace-pre-wrap">
                    {selectedDoc.content || 'Document content loading...'}
                  </div>
                ) : (
                  <div className="space-y-3">
                    {selectedDoc.chunks?.map((chunk, cIdx) => (
                      <div
                        key={cIdx}
                        className="p-3.5 rounded-xl bg-obsidian-950 border border-border/70 text-xs font-mono space-y-1.5"
                      >
                        <div className="flex items-center justify-between text-sovereign-amber text-[11px]">
                          <span>Chunk #{chunk.chunk_id}</span>
                          <span className="text-slate-500 font-sans">{chunk.section}</span>
                        </div>
                        <p className="text-slate-300 font-sans text-xs leading-relaxed">
                          {chunk.text}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="p-12 text-center text-xs font-mono text-slate-500">
              Loading policy document...
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
