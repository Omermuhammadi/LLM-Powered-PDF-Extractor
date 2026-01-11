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

export interface ValidationSummary {
  is_valid: boolean;
  overall_score: number;
  field_scores?: Record<string, number>;
  issues?: string[];
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
  file: File | null;
  progress: number;
  status: 'idle' | 'uploading' | 'processing' | 'success' | 'error';
  error?: string;
  result?: ExtractionResponse;
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
  subtotal?: number;
  tax_amount?: number;
  total_amount?: number;
  currency?: string;
  payment_terms?: string;
  line_items?: LineItem[];
}

export interface LineItem {
  description?: string;
  quantity?: number;
  unit_price?: number;
  amount?: number;
}
