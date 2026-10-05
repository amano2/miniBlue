import React, { useState } from 'react';
import { Copy, Check, Hash } from 'lucide-react';

interface HashChipProps {
  hash: string;
  truncateLength?: number;
  labelPrefix?: string;
  className?: string;
}

export const HashChip: React.FC<HashChipProps> = ({
  hash,
  truncateLength = 8,
  labelPrefix,
  className = '',
}) => {
  const [copied, setCopied] = useState(false);

  const displayHash = hash && hash.length > truncateLength * 2
    ? `${hash.slice(0, truncateLength)}...${hash.slice(-truncateLength)}`
    : hash || '0'.repeat(16);

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(hash);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button
      onClick={handleCopy}
      title={`Click to copy SHA-256 hash: ${hash}`}
      className={`group inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-obsidian-950/80 hover:bg-obsidian-900 border border-border hover:border-sovereign-amber/50 font-mono text-[11px] text-slate-400 hover:text-sovereign-amber transition-all cursor-pointer ${className}`}
    >
      <Hash className="w-3 h-3 text-slate-500 group-hover:text-sovereign-amber" />
      {labelPrefix && <span className="text-slate-500">{labelPrefix}</span>}
      <span className="tabular-nums tracking-wider">{displayHash}</span>
      {copied ? (
        <Check className="w-3 h-3 text-emerald-400 ml-0.5" />
      ) : (
        <Copy className="w-3 h-3 text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity ml-0.5" />
      )}
    </button>
  );
};
