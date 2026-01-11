import { useState, useEffect } from 'react';
import { FileText, Circle, Loader2 } from 'lucide-react';
import { getHealth } from '../services/api';

export function Header() {
  const [status, setStatus] = useState<'checking' | 'healthy' | 'unhealthy'>('checking');

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Check every 30s
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    try {
      const health = await getHealth();
      setStatus(health.status === 'healthy' ? 'healthy' : 'unhealthy');
    } catch {
      setStatus('unhealthy');
    }
  };

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
      <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
            <FileText className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-slate-900">
              PDF Intelligence Extractor
            </h1>
            <p className="text-xs text-slate-500">
              Extract structured data from PDFs using AI
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-sm">
          {status === 'checking' ? (
            <Loader2 className="w-4 h-4 text-slate-400 animate-spin" />
          ) : (
            <Circle
              className={`w-2.5 h-2.5 ${
                status === 'healthy' ? 'text-green-500 fill-green-500' : 'text-red-500 fill-red-500'
              }`}
            />
          )}
          <span className="text-slate-600">
            {status === 'checking'
              ? 'Checking...'
              : status === 'healthy'
              ? 'AI Ready'
              : 'AI Offline'}
          </span>
        </div>
      </div>
    </header>
  );
}
