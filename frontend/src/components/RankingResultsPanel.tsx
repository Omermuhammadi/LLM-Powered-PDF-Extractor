import { useState } from 'react';
import {
  ArrowLeft,
  ChevronDown,
  ChevronUp,
  Check,
  X,
  AlertTriangle,
  User,
  Briefcase,
  Clock,
  Award,
} from 'lucide-react';
import type {
  RankingResult,
  CandidateRankingScore,
  FullCandidateAnalysis,
  RecommendationType
} from '../types';

interface RankingResultsPanelProps {
  result: RankingResult;
  onBack: () => void;
}

// Minimal color palette - only 4 colors
const COLORS = {
  primary: '#0EA5E9',     // Soft teal/blue for positive
  warning: '#F59E0B',     // Soft orange for concerns
  danger: '#EF4444',      // Muted red for critical only
  success: '#10B981',     // Green only for 90+ scores
};

// Score ring component - clean circular progress
function ScoreRing({
  score,
  size = 80,
  strokeWidth = 6
}: {
  score: number;
  size?: number;
  strokeWidth?: number;
}) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (score / 100) * circumference;

  const getColor = (s: number) => {
    if (s >= 90) return COLORS.success;
    if (s >= 70) return COLORS.primary;
    if (s >= 50) return COLORS.warning;
    return COLORS.danger;
  };

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg className="transform -rotate-90" width={size} height={size}>
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-gray-200 dark:text-gray-700"
        />
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={getColor(score)}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-500 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span
          className="font-bold text-gray-900 dark:text-gray-100"
          style={{ fontSize: size * 0.35 }}
        >
          {score}
        </span>
      </div>
    </div>
  );
}

// Recommendation banner - prominent and clear
function RecommendationBanner({
  recommendation,
  text
}: {
  recommendation: RecommendationType;
  text: string;
}) {
  const config: Record<RecommendationType, { bg: string; border: string; text: string; label: string }> = {
    strong_hire: {
      bg: 'bg-emerald-50 dark:bg-emerald-900/20',
      border: 'border-emerald-200 dark:border-emerald-800',
      text: 'text-emerald-700 dark:text-emerald-300',
      label: '✓ Strong Recommendation'
    },
    good_fit: {
      bg: 'bg-sky-50 dark:bg-sky-900/20',
      border: 'border-sky-200 dark:border-sky-800',
      text: 'text-sky-700 dark:text-sky-300',
      label: '✓ Good Fit'
    },
    potential_fit: {
      bg: 'bg-amber-50 dark:bg-amber-900/20',
      border: 'border-amber-200 dark:border-amber-800',
      text: 'text-amber-700 dark:text-amber-300',
      label: '○ Potential Fit - Consider'
    },
    needs_review: {
      bg: 'bg-orange-50 dark:bg-orange-900/20',
      border: 'border-orange-200 dark:border-orange-800',
      text: 'text-orange-700 dark:text-orange-300',
      label: '! Needs Further Review'
    },
    not_recommended: {
      bg: 'bg-red-50 dark:bg-red-900/20',
      border: 'border-red-200 dark:border-red-800',
      text: 'text-red-700 dark:text-red-300',
      label: '✗ Not Recommended'
    },
  };

  const c = config[recommendation];

  return (
    <div className={`${c.bg} ${c.border} border rounded-lg p-4`}>
      <div className={`font-semibold ${c.text} text-lg`}>{c.label}</div>
      <p className="text-gray-600 dark:text-gray-400 mt-1 text-sm leading-relaxed">{text}</p>
    </div>
  );
}

// Clean skills display - two columns with icons
function SkillsSection({
  matched,
  missing
}: {
  matched: string[];
  missing: string[];
}) {
  const [showAllMatched, setShowAllMatched] = useState(false);
  const [showAllMissing, setShowAllMissing] = useState(false);

  const displayedMatched = showAllMatched ? matched : matched.slice(0, 6);
  const displayedMissing = showAllMissing ? missing : missing.slice(0, 6);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* Matched Skills */}
      <div>
        <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">
          Matched Skills ({matched.length})
        </h4>
        <ul className="space-y-2">
          {displayedMatched.map((skill, i) => (
            <li key={i} className="flex items-center gap-2 text-gray-700 dark:text-gray-300">
              <Check className="w-4 h-4 flex-shrink-0" style={{ color: COLORS.primary }} />
              <span className="text-sm">{skill}</span>
            </li>
          ))}
        </ul>
        {matched.length > 6 && (
          <button
            onClick={() => setShowAllMatched(!showAllMatched)}
            className="mt-2 text-sm text-sky-600 hover:text-sky-700 dark:text-sky-400"
          >
            {showAllMatched ? 'Show less' : `+${matched.length - 6} more`}
          </button>
        )}
      </div>

      {/* Missing Skills */}
      <div>
        <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">
          Missing Skills ({missing.length})
        </h4>
        <ul className="space-y-2">
          {displayedMissing.map((skill, i) => (
            <li key={i} className="flex items-center gap-2 text-gray-700 dark:text-gray-300">
              <X className="w-4 h-4 flex-shrink-0" style={{ color: COLORS.warning }} />
              <span className="text-sm">{skill}</span>
            </li>
          ))}
        </ul>
        {missing.length > 6 && (
          <button
            onClick={() => setShowAllMissing(!showAllMissing)}
            className="mt-2 text-sm text-sky-600 hover:text-sky-700 dark:text-sky-400"
          >
            {showAllMissing ? 'Show less' : `+${missing.length - 6} more`}
          </button>
        )}
      </div>
    </div>
  );
}

// Red flags alert banner - collapsible
function RedFlagsSection({
  analysis
}: {
  analysis: FullCandidateAnalysis;
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const redFlags = analysis.fit_analysis?.red_flags || [];

  if (redFlags.length === 0) return null;

  const hasCritical = redFlags.some(f => f.severity === 'high');
  const bgColor = hasCritical
    ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
    : 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800';
  const iconColor = hasCritical ? COLORS.danger : COLORS.warning;

  return (
    <div className={`${bgColor} border rounded-lg overflow-hidden`}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 flex items-center justify-between text-left"
      >
        <div className="flex items-center gap-3">
          <AlertTriangle className="w-5 h-5" style={{ color: iconColor }} />
          <span className="font-medium text-gray-800 dark:text-gray-200">
            {redFlags.length} {redFlags.length === 1 ? 'Concern' : 'Concerns'} Detected
            {hasCritical && <span className="text-red-600 ml-2">(Critical)</span>}
          </span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-5 h-5 text-gray-400" />
        ) : (
          <ChevronDown className="w-5 h-5 text-gray-400" />
        )}
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 space-y-3">
          {redFlags.map((flag, i) => (
            <div key={i} className="flex items-start gap-3">
              <AlertTriangle
                className="w-4 h-4 mt-0.5 flex-shrink-0"
                style={{ color: flag.severity === 'high' ? COLORS.danger : COLORS.warning }}
              />
              <div>
                <div className="font-medium text-gray-800 dark:text-gray-200 text-sm">
                  {flag.title}
                </div>
                <div className="text-gray-600 dark:text-gray-400 text-sm mt-0.5">
                  {flag.description}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Candidate card - clean and scannable
function CandidateCard({
  candidate,
  analysis,
  rank,
  isExpanded,
  onToggle,
}: {
  candidate: CandidateRankingScore;
  analysis?: FullCandidateAnalysis;
  rank: number;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const isTopCandidate = rank === 1;

  return (
    <div className={`
      bg-white dark:bg-gray-800 rounded-xl overflow-hidden transition-all duration-200
      ${isTopCandidate
        ? 'ring-2 ring-sky-500 shadow-lg'
        : 'border border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
      }
    `}>
      {/* Card Header - always visible */}
      <div
        className="p-6 cursor-pointer"
        onClick={onToggle}
      >
        <div className="flex items-start gap-6">
          {/* Score Ring */}
          <div className="flex-shrink-0">
            <ScoreRing score={candidate.overall_score} size={72} strokeWidth={5} />
          </div>

          {/* Candidate Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              {isTopCandidate && (
                <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-sky-100 dark:bg-sky-900/30 text-sky-700 dark:text-sky-300">
                  TOP CANDIDATE
                </span>
              )}
              <span className="text-xs text-gray-400 dark:text-gray-500">
                #{rank}
              </span>
            </div>

            <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 truncate">
              {candidate.candidate_name || 'Unknown Candidate'}
            </h3>

            <p className="text-sm text-gray-500 dark:text-gray-400 truncate mt-1">
              {candidate.file_name}
            </p>

            {/* Quick stats */}
            <div className="flex items-center gap-4 mt-3 text-sm">
              <span className="text-gray-600 dark:text-gray-400">
                ATS: <span className="font-medium text-gray-900 dark:text-gray-200">{candidate.ats_score}</span>
              </span>
              <span className="text-gray-600 dark:text-gray-400">
                Fit: <span className="font-medium text-gray-900 dark:text-gray-200">{candidate.fit_score}</span>
              </span>
              {candidate.suggested_level && (
                <span className="text-gray-600 dark:text-gray-400">
                  Level: <span className="font-medium text-gray-900 dark:text-gray-200">{candidate.suggested_level}</span>
                </span>
              )}
            </div>
          </div>

          {/* Expand indicator */}
          <div className="flex-shrink-0 text-gray-400">
            {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </div>
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && analysis && (
        <div className="border-t border-gray-100 dark:border-gray-700">
          {/* Executive Summary */}
          {candidate.executive_summary && (
            <div className="p-6 border-b border-gray-100 dark:border-gray-700">
              <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">
                Executive Summary
              </h4>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                {candidate.executive_summary}
              </p>
            </div>
          )}

          {/* Recommendation Banner */}
          {analysis.fit_analysis && (
            <div className="p-6 border-b border-gray-100 dark:border-gray-700">
              <RecommendationBanner
                recommendation={analysis.fit_analysis.recommendation}
                text={analysis.fit_analysis.recommendation_text}
              />
            </div>
          )}

          {/* Skills */}
          <div className="p-6 border-b border-gray-100 dark:border-gray-700">
            <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-4">
              Skills Analysis
            </h4>
            <SkillsSection
              matched={analysis.matched_skills}
              missing={analysis.missing_skills}
            />
          </div>

          {/* Red Flags */}
          {analysis.fit_analysis && analysis.fit_analysis.red_flags.length > 0 && (
            <div className="p-6 border-b border-gray-100 dark:border-gray-700">
              <RedFlagsSection analysis={analysis} />
            </div>
          )}

          {/* Strengths */}
          {analysis.fit_analysis && analysis.fit_analysis.strengths.length > 0 && (
            <div className="p-6 border-b border-gray-100 dark:border-gray-700">
              <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">
                Key Strengths
              </h4>
              <ul className="space-y-2">
                {analysis.fit_analysis.strengths.slice(0, 4).map((strength, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <Check className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: COLORS.success }} />
                    <span className="text-sm text-gray-700 dark:text-gray-300">{strength.title}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Interview Questions */}
          {analysis.fit_analysis && analysis.fit_analysis.interview_questions.length > 0 && (
            <div className="p-6">
              <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">
                Suggested Interview Questions
              </h4>
              <ol className="space-y-2 list-decimal list-inside">
                {analysis.fit_analysis.interview_questions.slice(0, 3).map((q, i) => (
                  <li key={i} className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                    {q}
                  </li>
                ))}
              </ol>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Main component
export function RankingResultsPanel({ result, onBack }: RankingResultsPanelProps) {
  const [expandedIndex, setExpandedIndex] = useState<number>(0);

  if (!result.success) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 mb-6"
        >
          <ArrowLeft className="w-5 h-5" />
          Back
        </button>
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-8 text-center">
          <AlertTriangle className="w-12 h-12 mx-auto mb-4" style={{ color: COLORS.danger }} />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">Analysis Failed</h2>
          <p className="text-gray-600 dark:text-gray-400">{result.error || 'An unknown error occurred'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Back Button */}
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 mb-8 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span className="text-sm">Back to Analyzer</span>
      </button>

      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          Candidate Rankings
        </h1>
        <div className="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
          {result.job_title && (
            <span className="flex items-center gap-1.5">
              <Briefcase className="w-4 h-4" />
              {result.job_title}
            </span>
          )}
          <span className="flex items-center gap-1.5">
            <User className="w-4 h-4" />
            {result.total_candidates} candidates
          </span>
          <span className="flex items-center gap-1.5">
            <Clock className="w-4 h-4" />
            {(result.processing_time_ms / 1000).toFixed(1)}s
          </span>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
          <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {result.total_candidates}
          </div>
          <div className="text-sm text-gray-500 dark:text-gray-400">Total</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
          <div className="text-2xl font-bold" style={{ color: COLORS.success }}>
            {(result.score_distribution.excellent || 0) + (result.score_distribution.good || 0)}
          </div>
          <div className="text-sm text-gray-500 dark:text-gray-400">Strong (70+)</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
          <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {result.average_score.toFixed(0)}
          </div>
          <div className="text-sm text-gray-500 dark:text-gray-400">Avg Score</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
          <div className="text-2xl font-bold" style={{ color: COLORS.primary }}>
            {result.top_candidate?.overall_score || 0}
          </div>
          <div className="text-sm text-gray-500 dark:text-gray-400">Top Score</div>
        </div>
      </div>

      {/* Hiring Recommendation */}
      <div className={`
        mb-8 p-5 rounded-xl border-l-4
        ${result.hiring_recommendation.includes('STRONG') || result.hiring_recommendation.includes('GOOD')
          ? 'bg-emerald-50 dark:bg-emerald-900/10 border-emerald-500'
          : result.hiring_recommendation.includes('ACCEPTABLE')
            ? 'bg-amber-50 dark:bg-amber-900/10 border-amber-500'
            : 'bg-red-50 dark:bg-red-900/10 border-red-500'
        }
      `}>
        <div className="flex items-start gap-3">
          <Award className="w-5 h-5 mt-0.5 flex-shrink-0" style={{
            color: result.hiring_recommendation.includes('STRONG') || result.hiring_recommendation.includes('GOOD')
              ? COLORS.success
              : result.hiring_recommendation.includes('ACCEPTABLE')
                ? COLORS.warning
                : COLORS.danger
          }} />
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-gray-100">Hiring Recommendation</h3>
            <p className="text-gray-600 dark:text-gray-400 mt-1 leading-relaxed">{result.hiring_recommendation}</p>
          </div>
        </div>
      </div>

      {/* Candidate List */}
      <div className="space-y-4">
        {result.rankings.map((candidate, index) => (
          <CandidateCard
            key={candidate.file_name}
            candidate={candidate}
            analysis={result.all_analyses[candidate.file_name]}
            rank={index + 1}
            isExpanded={expandedIndex === index}
            onToggle={() => setExpandedIndex(expandedIndex === index ? -1 : index)}
          />
        ))}
      </div>
    </div>
  );
}
