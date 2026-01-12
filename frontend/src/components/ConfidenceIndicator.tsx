import clsx from 'clsx';

interface ConfidenceIndicatorProps {
  score: number; // 0-1
  label?: string;
  showPercentage?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

// Safe number conversion to handle undefined/null/NaN
function safeScore(score: unknown): number {
  if (score === undefined || score === null) return 0;
  const num = typeof score === 'number' ? score : parseFloat(String(score));
  if (isNaN(num)) return 0;
  return Math.max(0, Math.min(1, num)); // Clamp between 0 and 1
}

export function ConfidenceIndicator({
  score: rawScore,
  label,
  showPercentage = true,
  size = 'md',
}: ConfidenceIndicatorProps) {
  const score = safeScore(rawScore);
  const percentage = Math.round(score * 100);

  const getColor = () => {
    if (score >= 0.8) return 'text-green-600 bg-green-100';
    if (score >= 0.5) return 'text-amber-600 bg-amber-100';
    return 'text-red-600 bg-red-100';
  };

  const getBarColor = () => {
    if (score >= 0.8) return 'bg-green-500';
    if (score >= 0.5) return 'bg-amber-500';
    return 'bg-red-500';
  };

  const getLabel = () => {
    if (score >= 0.8) return 'High';
    if (score >= 0.5) return 'Medium';
    return 'Low';
  };

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-2.5 py-1',
    lg: 'text-base px-3 py-1.5',
  };

  return (
    <div className="flex items-center gap-2">
      {label && <span className="text-slate-600 text-sm">{label}</span>}

      <div className="flex items-center gap-2">
        {/* Bar indicator */}
        <div className="w-16 h-1.5 bg-slate-200 rounded-full overflow-hidden">
          <div
            className={clsx('h-full rounded-full transition-all', getBarColor())}
            style={{ width: `${percentage}%` }}
          />
        </div>

        {/* Badge */}
        <span
          className={clsx(
            'font-medium rounded-full',
            getColor(),
            sizeClasses[size]
          )}
        >
          {showPercentage ? `${percentage}%` : getLabel()}
        </span>
      </div>
    </div>
  );
}

interface ValidationScoreProps {
  score: number;
  isValid: boolean;
  fieldsExtracted?: number;
  fieldsExpected?: number;
}

export function ValidationScore({
  score: rawScore,
  isValid: _isValid, // Available for future use
  fieldsExtracted,
  fieldsExpected,
}: ValidationScoreProps) {
  const score = safeScore(rawScore);
  const percentage = Math.round(score * 100);

  // Calculate display values - use sensible defaults if not provided
  const displayExtracted = fieldsExtracted ?? (percentage > 0 ? Math.round(percentage / 10) : 0);
  const displayExpected = fieldsExpected ?? 10;

  return (
    <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
      <div className="flex items-center gap-3">
        <div
          className={clsx(
            'w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm',
            percentage >= 80 ? 'bg-green-500' : percentage >= 50 ? 'bg-amber-500' : 'bg-red-500'
          )}
        >
          {percentage}
        </div>
        <div>
          <p className="font-medium text-slate-900">
            {percentage >= 80 ? 'Excellent' : percentage >= 60 ? 'Good' : percentage >= 40 ? 'Needs Review' : 'Low Confidence'}
          </p>
          <p className="text-sm text-slate-500">
            {displayExtracted > 0 ? `${displayExtracted} fields extracted` : `Confidence: ${percentage}%`}
          </p>
        </div>
      </div>
      <ConfidenceIndicator score={score} showPercentage={false} />
    </div>
  );
}
