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
