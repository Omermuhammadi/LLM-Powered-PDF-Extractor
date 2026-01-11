import clsx from 'clsx';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';

interface ProgressBarProps {
  progress: number;
  status: 'idle' | 'uploading' | 'processing' | 'success' | 'error';
  statusText?: string;
}

export function ProgressBar({ progress, status, statusText }: ProgressBarProps) {
  const getStatusColor = () => {
    switch (status) {
      case 'success':
        return 'bg-green-500';
      case 'error':
        return 'bg-red-500';
      case 'processing':
        return 'bg-amber-500';
      default:
        return 'bg-blue-500';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'processing':
      case 'uploading':
        return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
      default:
        return null;
    }
  };

  const getDefaultStatusText = () => {
    switch (status) {
      case 'uploading':
        return 'Uploading file...';
      case 'processing':
        return 'Processing with AI...';
      case 'success':
        return 'Extraction complete!';
      case 'error':
        return 'Extraction failed';
      default:
        return '';
    }
  };

  if (status === 'idle') {
    return null;
  }

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {getStatusIcon()}
          <span
            className={clsx('text-sm font-medium', {
              'text-green-600': status === 'success',
              'text-red-600': status === 'error',
              'text-slate-700': status !== 'success' && status !== 'error',
            })}
          >
            {statusText || getDefaultStatusText()}
          </span>
        </div>
        <span className="text-sm text-slate-500">{progress}%</span>
      </div>

      <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
        <div
          className={clsx(
            'h-full transition-all duration-300 ease-out rounded-full',
            getStatusColor(),
            {
              'animate-pulse': status === 'processing',
            }
          )}
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
