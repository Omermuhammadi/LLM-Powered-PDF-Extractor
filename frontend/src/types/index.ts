// API Response Types

export interface ExtractionResponse {
  request_id: string;
  timestamp: string;
  status: 'success' | 'failed' | 'processing';
  stage: string;
  document?: DocumentMetadata;
  extracted_data?: Record<string, unknown>;
  raw_extraction?: Record<string, unknown>;
  validation?: ValidationSummary;
  metrics?: ExtractionMetrics;
  warnings?: string[];
  error?: ExtractionError;
}

export interface DocumentMetadata {
  filename: string;
  file_size?: number;
  page_count: number;
  detected_type: string;
  detection_confidence: number;
  total_chars?: number;
  total_words?: number;
}

export interface ValidationIssue {
  field_name: string;
  is_valid: boolean;
  severity: 'critical' | 'warning' | 'info';
  message: string;
  suggestion?: string | null;
}

export interface FieldScore {
  field_name: string;
  score: number;
  confidence: 'high' | 'medium' | 'low' | 'unknown';
  extracted_value?: string | null;
  source: string;
  warnings: string[];
}

export interface ValidationSummary {
  is_valid: boolean;
  overall_score: number;
  field_scores?: FieldScore[];
  issues?: ValidationIssue[];
  critical_issues?: number;
  warning_issues?: number;
  fields_extracted?: number;
  fields_expected?: number;
}

export interface ExtractionMetrics {
  pdf_extraction_time?: number;
  text_processing_time?: number;
  document_detection_time?: number;
  llm_extraction_time?: number;
  total_time?: number;
  tokens_used?: number;
  tokens_per_second?: number;
}

export interface ExtractionError {
  code: string;
  message: string;
  stage?: string;
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  version: string;
  uptime_seconds: number;
  components?: ComponentStatus[];
  system?: Record<string, unknown>;
}

export interface ComponentStatus {
  name: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  latency_ms?: number;
  message?: string;
  details?: Record<string, unknown>;
}

// Upload state types
export interface UploadState {
  files: File[];
  progress: number;
  status: 'idle' | 'uploading' | 'processing' | 'success' | 'error';
  error?: string;
  result?: ExtractionResponse;
  batchResult?: BatchExtractionResponse;
}

// Batch extraction response
export interface BatchExtractionResponse {
  batch_id: string;
  total_files: number;
  successful: number;
  failed: number;
  total_time: number;
  results: ExtractionResponse[];
}

// Invoice data type
export interface InvoiceData {
  invoice_number?: string;
  invoice_date?: string;
  due_date?: string;
  vendor_name?: string;
  vendor_address?: string;
  vendor_email?: string;
  vendor_phone?: string;
  customer_name?: string;
  customer_address?: string;
  customer_email?: string;
  bill_to?: string;
  ship_to?: string;
  subtotal?: number;
  tax_amount?: number;
  tax_rate?: number;
  discount_amount?: number;
  discount_percentage?: number;
  shipping_amount?: number;
  total_amount?: number;
  currency?: string;
  payment_terms?: string;
  payment_method?: string;
  notes?: string;
  order_id?: string;
  amount_paid?: number;
  balance_due?: number;
  line_items?: LineItem[];
}

export interface LineItem {
  description?: string;
  quantity?: number;
  unit_price?: number;
  price?: number;  // alias for unit_price
  amount?: number;
}

// Resume Analyzer Types
export type RecommendationType =
  | 'strong_hire'
  | 'good_fit'
  | 'potential_fit'
  | 'needs_review'
  | 'not_recommended';

export type RedFlagSeverity = 'high' | 'medium' | 'low';

export type RedFlagType =
  | 'short_tenure'
  | 'employment_gap'
  | 'overqualified'
  | 'underqualified'
  | 'frequent_job_changes'
  | 'career_regression'
  | 'overlapping_jobs'
  | 'missing_recent_experience'
  | 'no_progression'
  | 'education_mismatch'
  | 'skill_gaps'
  | 'other';

export interface RedFlag {
  flag_type: RedFlagType;
  severity: RedFlagSeverity;
  title: string;
  description: string;
  evidence?: string | null;
  suggestion?: string | null;
}

export interface StrengthItem {
  category: string;
  title: string;
  description: string;
  relevance_score: number;
}

export interface CareerProgression {
  trajectory: string;
  avg_tenure_months: number;
  longest_tenure_months: number;
  total_companies: number;
  has_leadership_progression: boolean;
  progression_summary: string;
}

export interface FitScoreBreakdown {
  skills_alignment: number;
  experience_match: number;
  education_fit: number;
  career_trajectory: number;
  cultural_signals: number;
}

export interface CandidateFitResult {
  fit_score: number;
  fit_score_breakdown?: FitScoreBreakdown | null;
  recommendation: RecommendationType;
  recommendation_text: string;
  strengths: StrengthItem[];
  weaknesses: string[];
  red_flags: RedFlag[];
  red_flag_count: number;
  has_critical_red_flags: boolean;
  career_progression?: CareerProgression | null;
  executive_summary: string;
  interview_questions: string[];
  suggested_level?: string | null;
  analysis_confidence: number;
}

export interface FullCandidateAnalysis {
  success: boolean;
  candidate_name?: string | null;
  candidate_email?: string | null;
  candidate_current_role?: string | null;
  candidate_experience_years?: number | null;
  job_title?: string | null;
  company_name?: string | null;
  overall_score: number;
  ats_score: number;
  matched_skills: string[];
  missing_skills: string[];
  fit_analysis?: CandidateFitResult | null;
  resume_data: Record<string, unknown>;
  jd_data: Record<string, unknown>;
  processing_time_ms: number;
  error?: string | null;
}

export interface CandidateRankingScore {
  rank: number;
  file_name: string;
  candidate_name?: string | null;
  overall_score: number;
  ats_score: number;
  fit_score: number;
  recommendation: RecommendationType;
  strengths_count: number;
  red_flags_count: number;
  has_critical_red_flags: boolean;
  suggested_level?: string | null;
  executive_summary?: string | null;
}

export interface CandidateComparison {
  file_name_1: string;
  file_name_2: string;
  overall_score_1: number;
  overall_score_2: number;
  overall_score_diff: number;
  ats_score_1: number;
  ats_score_2: number;
  fit_score_1: number;
  fit_score_2: number;
  matched_skills_1: string[];
  matched_skills_2: string[];
  unique_skills_1: string[];
  unique_skills_2: string[];
  common_skills: string[];
  red_flags_1: number;
  red_flags_2: number;
  critical_flags_1: boolean;
  critical_flags_2: boolean;
  recommendation_1: RecommendationType;
  recommendation_2: RecommendationType;
  winner: number;
  winner_reason: string;
}

export interface RankingResult {
  success: boolean;
  job_title?: string | null;
  company_name?: string | null;
  total_candidates: number;
  rankings: CandidateRankingScore[];
  top_candidate?: CandidateRankingScore | null;
  top_candidate_analysis?: FullCandidateAnalysis | null;
  all_analyses: Record<string, FullCandidateAnalysis>;
  score_distribution: Record<string, number>;
  average_score: number;
  hiring_recommendation: string;
  processing_time_ms: number;
  error?: string | null;
}

// Resume Analyzer State
export interface ResumeAnalyzerState {
  mode: 'idle' | 'uploading' | 'analyzing' | 'complete' | 'error';
  jobDescriptionText: string;
  resumeFiles: File[];
  rankingResult?: RankingResult;
  error?: string;
  progress: number;
}
