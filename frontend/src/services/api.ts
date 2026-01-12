import axios from 'axios';
import type { AxiosProgressEvent } from 'axios';
import type { ExtractionResponse, HealthResponse, BatchExtractionResponse } from '../types';

const API_BASE = '/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 600000, // 10 minutes for large multipage documents
});

export interface ExtractOptions {
  documentType?: string;
  validateOutput?: boolean;
  includeRawText?: boolean;
  onProgress?: (progress: number) => void;
}

export async function extractFromPdf(
  file: File,
  options: ExtractOptions = {}
): Promise<ExtractionResponse> {
  const formData = new FormData();
  formData.append('file', file);

  if (options.documentType) {
    formData.append('document_type', options.documentType);
  }
  formData.append('validate_output', String(options.validateOutput ?? true));
  formData.append('include_raw_text', String(options.includeRawText ?? false));

  const response = await api.post<ExtractionResponse>('/extract/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent: AxiosProgressEvent) => {
      if (progressEvent.total && options.onProgress) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        options.onProgress(Math.min(progress, 50)); // Upload is 0-50%
      }
    },
  });

  return response.data;
}

export async function extractFromPdfBatch(
  files: File[],
  options: ExtractOptions = {}
): Promise<BatchExtractionResponse> {
  const formData = new FormData();

  // Append all files
  files.forEach((file) => {
    formData.append('files', file);
  });

  if (options.documentType) {
    formData.append('document_type', options.documentType);
  }
  formData.append('validate_output', String(options.validateOutput ?? true));

  const response = await api.post<BatchExtractionResponse>('/extract/batch', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent: AxiosProgressEvent) => {
      if (progressEvent.total && options.onProgress) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        options.onProgress(Math.min(progress, 50)); // Upload is 0-50%
      }
    },
  });

  return response.data;
}

export async function extractTextOnly(file: File): Promise<{
  request_id: string;
  filename: string;
  success: boolean;
  page_count: number;
  total_chars: number;
  text_preview?: string;
  is_scanned: boolean;
  metadata: Record<string, unknown>;
}> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/extract/text', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await api.get<HealthResponse>('/health/');
  return response.data;
}

export async function getHealthInfo(): Promise<{
  name: string;
  version: string;
  api_version: string;
  llm: { mode: string; model: string };
  limits: {
    max_upload_size_mb: number;
    supported_formats: string[];
    timeout_seconds: number;
  };
  features: {
    document_types: string[];
    validation: boolean;
    batch_processing: boolean;
  };
}> {
  const response = await api.get('/health/info');
  return response.data;
}

export async function checkLlmHealth(): Promise<{
  name: string;
  status: string;
  latency_ms?: number;
  message?: string;
  details?: Record<string, unknown>;
}> {
  const response = await api.get('/health/llm');
  return response.data;
}

export default api;
