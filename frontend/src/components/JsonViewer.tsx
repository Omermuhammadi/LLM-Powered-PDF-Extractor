import { useState } from 'react';
import { ChevronDown, ChevronRight, Copy, Check } from 'lucide-react';


interface JsonViewerProps {
  data: unknown;
  title?: string;
  defaultExpanded?: boolean;
  maxDepth?: number;
}

export function JsonViewer({
  data,
  title,
  defaultExpanded = true,
  maxDepth = 5,
}: JsonViewerProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(data, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };

  return (
    <div className="bg-slate-900 rounded-lg overflow-hidden">
      {title && (
        <div className="flex items-center justify-between px-4 py-2 bg-slate-800 border-b border-slate-700">
          <span className="text-slate-300 text-sm font-medium">{title}</span>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 text-slate-400 hover:text-white transition-colors text-sm"
          >
            {copied ? (
              <>
                <Check className="w-4 h-4" />
                Copied!
              </>
            ) : (
              <>
                <Copy className="w-4 h-4" />
                Copy
              </>
            )}
          </button>
        </div>
      )}
      <div className="p-4 overflow-auto max-h-[500px] text-sm font-mono">
        <JsonNode data={data} depth={0} expanded={defaultExpanded} maxDepth={maxDepth} />
      </div>
    </div>
  );
}

interface JsonNodeProps {
  data: unknown;
  depth: number;
  expanded: boolean;
  maxDepth: number;
  keyName?: string;
}

function JsonNode({ data, depth, expanded, maxDepth, keyName }: JsonNodeProps) {
  const [isExpanded, setIsExpanded] = useState(expanded && depth < maxDepth);

  const indent = depth * 16;

  // Render primitive values
  if (data === null) {
    return (
      <span className="text-slate-500">
        {keyName && <span className="text-purple-400">"{keyName}"</span>}
        {keyName && <span className="text-white">: </span>}
        <span className="text-slate-500">null</span>
      </span>
    );
  }

  if (typeof data === 'boolean') {
    return (
      <span>
        {keyName && <span className="text-purple-400">"{keyName}"</span>}
        {keyName && <span className="text-white">: </span>}
        <span className="text-amber-400">{data.toString()}</span>
      </span>
    );
  }

  if (typeof data === 'number') {
    return (
      <span>
        {keyName && <span className="text-purple-400">"{keyName}"</span>}
        {keyName && <span className="text-white">: </span>}
        <span className="text-cyan-400">{data}</span>
      </span>
    );
  }

  if (typeof data === 'string') {
    return (
      <span>
        {keyName && <span className="text-purple-400">"{keyName}"</span>}
        {keyName && <span className="text-white">: </span>}
        <span className="text-green-400">"{data}"</span>
      </span>
    );
  }

  // Render arrays
  if (Array.isArray(data)) {
    if (data.length === 0) {
      return (
        <span>
          {keyName && <span className="text-purple-400">"{keyName}"</span>}
          {keyName && <span className="text-white">: </span>}
          <span className="text-white">[]</span>
        </span>
      );
    }

    return (
      <div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-1 text-white hover:text-blue-400 transition-colors"
        >
          {isExpanded ? (
            <ChevronDown className="w-3 h-3" />
          ) : (
            <ChevronRight className="w-3 h-3" />
          )}
          {keyName && <span className="text-purple-400">"{keyName}"</span>}
          {keyName && <span className="text-white">: </span>}
          <span className="text-white">[</span>
          {!isExpanded && (
            <span className="text-slate-500 text-xs ml-1">
              {data.length} items
            </span>
          )}
        </button>
        {isExpanded && (
          <div style={{ marginLeft: indent + 16 }}>
            {data.map((item, index) => (
              <div key={index} className="my-1">
                <JsonNode
                  data={item}
                  depth={depth + 1}
                  expanded={expanded}
                  maxDepth={maxDepth}
                />
                {index < data.length - 1 && <span className="text-white">,</span>}
              </div>
            ))}
          </div>
        )}
        {isExpanded && <span className="text-white">]</span>}
      </div>
    );
  }

  // Render objects
  if (typeof data === 'object') {
    const entries = Object.entries(data);
    if (entries.length === 0) {
      return (
        <span>
          {keyName && <span className="text-purple-400">"{keyName}"</span>}
          {keyName && <span className="text-white">: </span>}
          <span className="text-white">{'{}'}</span>
        </span>
      );
    }

    return (
      <div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-1 text-white hover:text-blue-400 transition-colors"
        >
          {isExpanded ? (
            <ChevronDown className="w-3 h-3" />
          ) : (
            <ChevronRight className="w-3 h-3" />
          )}
          {keyName && <span className="text-purple-400">"{keyName}"</span>}
          {keyName && <span className="text-white">: </span>}
          <span className="text-white">{'{'}</span>
          {!isExpanded && (
            <span className="text-slate-500 text-xs ml-1">
              {entries.length} fields
            </span>
          )}
        </button>
        {isExpanded && (
          <div style={{ marginLeft: indent + 16 }}>
            {entries.map(([key, value], index) => (
              <div key={key} className="my-1">
                <JsonNode
                  data={value}
                  depth={depth + 1}
                  expanded={expanded}
                  maxDepth={maxDepth}
                  keyName={key}
                />
                {index < entries.length - 1 && <span className="text-white">,</span>}
              </div>
            ))}
          </div>
        )}
        {isExpanded && <span className="text-white">{'}'}</span>}
      </div>
    );
  }

  return <span className="text-slate-500">{String(data)}</span>;
}
