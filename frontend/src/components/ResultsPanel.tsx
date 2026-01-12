import { useState } from 'react';
import {
  FileText,
  Clock,
  Zap,
  CheckCircle,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Download,
} from 'lucide-react';
import clsx from 'clsx';
import type { ExtractionResponse, InvoiceData } from '../types';
import { JsonViewer } from './JsonViewer';
import { ConfidenceIndicator, ValidationScore } from './ConfidenceIndicator';

interface ResultsPanelProps {
  result: ExtractionResponse;
}

// Safe number formatter - handles undefined, null, and non-numbers
function safeToFixed(value: unknown, decimals: number = 2): string {
  if (value === undefined || value === null) return '—';
  const num = typeof value === 'number' ? value : parseFloat(String(value));
  if (isNaN(num)) return '—';
  return num.toFixed(decimals);
}

// Safe currency formatter
function safeCurrency(value: unknown, currency: string = '$', decimals: number = 2): string {
  if (value === undefined || value === null) return '—';
  const num = typeof value === 'number' ? value : parseFloat(String(value));
  if (isNaN(num)) return '—';
  return `${currency}${num.toFixed(decimals)}`;
}

export function ResultsPanel({ result }: ResultsPanelProps) {
  const [activeTab, setActiveTab] = useState<'formatted' | 'raw'>('formatted');
  const [showMetrics, setShowMetrics] = useState(false);

  // Safely extract data with null checks
  const extractedData = result?.extracted_data as InvoiceData | undefined;

  const handleDownloadJson = () => {
    try {
      const blob = new Blob([JSON.stringify(result, null, 2)], {
        type: 'application/json',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `extraction_${result?.request_id || 'unknown'}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download JSON:', err);
    }
  };

  // Guard against null result
  if (!result) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 text-center">
        <p className="text-slate-500">No extraction results available.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {result.status === 'success' ? (
            <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
          ) : (
            <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-red-600" />
            </div>
          )}
          <div>
            <h2 className="font-semibold text-slate-900">Extraction Results</h2>
            <p className="text-sm text-slate-500">
              {result.document?.filename || 'Unknown file'} •{' '}
              {result.document?.detected_type || 'Unknown type'}
            </p>
          </div>
        </div>

        <button
          onClick={handleDownloadJson}
          className="flex items-center gap-2 px-3 py-1.5 text-sm text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
        >
          <Download className="w-4 h-4" />
          Download JSON
        </button>
      </div>

      {/* Document Info */}
      {result.document && (
        <div className="px-6 py-4 bg-slate-50 border-b border-slate-200">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-slate-400" />
              <div>
                <p className="text-xs text-slate-500">Pages</p>
                <p className="font-medium text-slate-900">
                  {result.document.page_count ?? '—'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-slate-400" />
              <div>
                <p className="text-xs text-slate-500">Document Type</p>
                <p className="font-medium text-slate-900 capitalize">
                  {result.document.detected_type || 'unknown'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-slate-400" />
              <div>
                <p className="text-xs text-slate-500">Processing Time</p>
                <p className="font-medium text-slate-900">
                  {safeToFixed(result.metrics?.total_time)}s
                </p>
              </div>
            </div>
            <div>
              <p className="text-xs text-slate-500 mb-1">Confidence</p>
              <ConfidenceIndicator
                score={result.document.detection_confidence ?? 0}
                size="sm"
              />
            </div>
          </div>
        </div>
      )}

      {/* Validation Summary */}
      {result.validation && (
        <div className="px-6 py-4 border-b border-slate-200">
          <ValidationScore
            score={result.validation.overall_score ?? 0}
            isValid={result.validation.is_valid ?? false}
            fieldsExtracted={result.validation.fields_extracted}
            fieldsExpected={result.validation.fields_expected}
          />
          {result.validation.issues && Array.isArray(result.validation.issues) && result.validation.issues.length > 0 && (
            <div className="mt-3 space-y-1">
              {result.validation.issues.map((issue, i) => (
                <div
                  key={i}
                  className={`flex items-center gap-2 text-sm ${
                    issue?.severity === 'critical' ? 'text-red-600' : 'text-amber-600'
                  }`}
                >
                  <AlertTriangle className="w-4 h-4" />
                  <span>{issue?.message || 'Unknown issue'}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tabs */}
      <div className="px-6 border-b border-slate-200">
        <div className="flex gap-4">
          <button
            onClick={() => setActiveTab('formatted')}
            className={clsx(
              'py-3 px-1 text-sm font-medium border-b-2 transition-colors',
              activeTab === 'formatted'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            )}
          >
            Formatted View
          </button>
          <button
            onClick={() => setActiveTab('raw')}
            className={clsx(
              'py-3 px-1 text-sm font-medium border-b-2 transition-colors',
              activeTab === 'raw'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            )}
          >
            Raw JSON
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {activeTab === 'formatted' ? (
          extractedData ? (
            <FormattedInvoiceView data={extractedData} />
          ) : (
            <div className="p-4 bg-slate-50 rounded-lg text-center text-slate-500">
              No structured data available. Switch to Raw JSON to see the extracted content.
            </div>
          )
        ) : (
          <JsonViewer data={result?.extracted_data || {}} title="Extracted Data" />
        )}
      </div>

      {/* Metrics (collapsible) */}
      {result.metrics && (
        <div className="border-t border-slate-200">
          <button
            onClick={() => setShowMetrics(!showMetrics)}
            className="w-full px-6 py-3 flex items-center justify-between text-sm text-slate-600 hover:bg-slate-50 transition-colors"
          >
            <span>Processing Metrics</span>
            {showMetrics ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>
          {showMetrics && (
            <div className="px-6 pb-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <MetricItem
                label="PDF Extraction"
                value={result.metrics.pdf_extraction_time}
                unit="s"
              />
              <MetricItem
                label="Text Processing"
                value={result.metrics.text_processing_time}
                unit="s"
              />
              <MetricItem
                label="LLM Extraction"
                value={result.metrics.llm_extraction_time}
                unit="s"
              />
              <MetricItem
                label="Tokens/sec"
                value={result.metrics.tokens_per_second}
                unit=""
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function MetricItem({
  label,
  value,
  unit,
}: {
  label: string;
  value?: number;
  unit: string;
}) {
  return (
    <div>
      <p className="text-slate-500 text-xs">{label}</p>
      <p className="font-medium text-slate-900">
        {safeToFixed(value)}
        {value !== undefined && !isNaN(Number(value)) ? unit : ''}
      </p>
    </div>
  );
}

function FormattedInvoiceView({ data }: { data: InvoiceData }) {
  // Guard against null/undefined data
  if (!data || typeof data !== 'object') {
    return (
      <div className="p-4 bg-slate-50 rounded-lg text-center text-slate-500">
        No invoice data available.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Fields */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <FieldDisplay label="Invoice Number" value={data.invoice_number} />
        <FieldDisplay label="Invoice Date" value={data.invoice_date} />
        <FieldDisplay label="Due Date" value={data.due_date} />
        <FieldDisplay label="Order ID" value={data.order_id} />
      </div>

      {/* Vendor & Customer */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-4 bg-slate-50 rounded-lg">
          <h4 className="font-medium text-slate-900 mb-3">Vendor Information</h4>
          <div className="space-y-2">
            <FieldDisplay label="Name" value={data.vendor_name} />
            <FieldDisplay label="Address" value={data.vendor_address} />
            <FieldDisplay label="Email" value={data.vendor_email} />
            <FieldDisplay label="Phone" value={data.vendor_phone} />
          </div>
        </div>
        <div className="p-4 bg-slate-50 rounded-lg">
          <h4 className="font-medium text-slate-900 mb-3">Customer / Billing</h4>
          <div className="space-y-2">
            <FieldDisplay label="Bill To" value={data.bill_to || data.customer_name} />
            <FieldDisplay label="Ship To" value={data.ship_to || data.customer_address} />
          </div>
        </div>
      </div>

      {/* Notes */}
      {data.notes && (
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <h4 className="font-medium text-amber-800 mb-2">Notes</h4>
          <p className="text-sm text-amber-700">{data.notes}</p>
        </div>
      )}

      {/* Line Items */}
      {data.line_items && Array.isArray(data.line_items) && data.line_items.length > 0 && (
        <div>
          <h4 className="font-medium text-slate-900 mb-3">Line Items</h4>
          <div className="border border-slate-200 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="text-left px-4 py-2 text-slate-600 font-medium">
                    Description
                  </th>
                  <th className="text-right px-4 py-2 text-slate-600 font-medium">
                    Qty
                  </th>
                  <th className="text-right px-4 py-2 text-slate-600 font-medium">
                    Unit Price
                  </th>
                  <th className="text-right px-4 py-2 text-slate-600 font-medium">
                    Amount
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.line_items.map((item, i) => {
                  const unitPrice = item?.unit_price ?? item?.price;
                  return (
                    <tr key={i} className="border-t border-slate-200">
                      <td className="px-4 py-2 text-slate-900">
                        {item?.description || '—'}
                      </td>
                      <td className="px-4 py-2 text-slate-900 text-right">
                        {item?.quantity ?? '—'}
                      </td>
                      <td className="px-4 py-2 text-slate-900 text-right">
                        {safeCurrency(unitPrice)}
                      </td>
                      <td className="px-4 py-2 text-slate-900 text-right font-medium">
                        {safeCurrency(item?.amount)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Totals */}
      <div className="flex justify-end">
        <div className="w-64 space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-slate-500">Subtotal</span>
            <span className="text-slate-900">
              {safeCurrency(data.subtotal, data.currency || '$')}
            </span>
          </div>
          {data.shipping_amount !== undefined && data.shipping_amount !== null && (
            <div className="flex justify-between text-sm">
              <span className="text-slate-500">Shipping</span>
              <span className="text-slate-900">
                {safeCurrency(data.shipping_amount, data.currency || '$')}
              </span>
            </div>
          )}
          <div className="flex justify-between text-sm">
            <span className="text-slate-500">Tax</span>
            <span className="text-slate-900">
              {safeCurrency(data.tax_amount, data.currency || '$')}
            </span>
          </div>
          <div className="flex justify-between text-lg font-semibold pt-2 border-t border-slate-200">
            <span className="text-slate-900">Total</span>
            <span className="text-blue-600">
              {safeCurrency(data.total_amount, data.currency || '$')}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

function FieldDisplay({
  label,
  value,
}: {
  label: string;
  value?: string | number;
}) {
  return (
    <div>
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-slate-900 font-medium">{value || '—'}</p>
    </div>
  );
}
