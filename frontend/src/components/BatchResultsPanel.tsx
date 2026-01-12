import { useState } from 'react';
import {
  FileText,
  CheckCircle,
  XCircle,
  ChevronDown,
  ChevronUp,
  Download,
  Clock,
  Files,
} from 'lucide-react';
import clsx from 'clsx';
import type { BatchExtractionResponse, ExtractionResponse, InvoiceData } from '../types';
import { JsonViewer } from './JsonViewer';
import { ConfidenceIndicator } from './ConfidenceIndicator';

interface BatchResultsPanelProps {
  batchResult: BatchExtractionResponse;
}

// Safe number formatter
function safeToFixed(value: unknown, decimals: number = 2): string {
  if (value === undefined || value === null) return '—';
  const num = typeof value === 'number' ? value : parseFloat(String(value));
  if (isNaN(num)) return '—';
  return num.toFixed(decimals);
}

function SingleResultCard({ result, index }: { result: ExtractionResponse; index: number }) {
  const [isExpanded, setIsExpanded] = useState(index === 0);
  const [showRaw, setShowRaw] = useState(false);

  const isSuccess = result.status === 'success';
  const extractedData = result?.extracted_data as InvoiceData | undefined;

  const handleDownloadJson = () => {
    const blob = new Blob([JSON.stringify(result, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `extraction_${result?.document?.filename || 'unknown'}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className={clsx(
      'border rounded-lg overflow-hidden',
      isSuccess ? 'border-slate-200' : 'border-red-200'
    )}>
      {/* Card Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={clsx(
          'w-full px-4 py-3 flex items-center justify-between transition-colors',
          isSuccess ? 'bg-slate-50 hover:bg-slate-100' : 'bg-red-50 hover:bg-red-100'
        )}
      >
        <div className="flex items-center gap-3">
          <div className={clsx(
            'w-8 h-8 rounded-full flex items-center justify-center',
            isSuccess ? 'bg-green-100' : 'bg-red-100'
          )}>
            {isSuccess ? (
              <CheckCircle className="w-4 h-4 text-green-600" />
            ) : (
              <XCircle className="w-4 h-4 text-red-600" />
            )}
          </div>
          <div className="text-left">
            <p className="font-medium text-slate-900">
              {result.document?.filename || `File ${index + 1}`}
            </p>
            <p className="text-sm text-slate-500">
              {isSuccess ? (
                <>
                  {result.document?.detected_type || 'Unknown'} •{' '}
                  {safeToFixed(result.metrics?.total_time)}s
                </>
              ) : (
                <span className="text-red-600">
                  {result.error?.message || 'Extraction failed'}
                </span>
              )}
            </p>
          </div>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-5 h-5 text-slate-400" />
        ) : (
          <ChevronDown className="w-5 h-5 text-slate-400" />
        )}
      </button>

      {/* Card Content */}
      {isExpanded && (
        <div className="p-4 border-t border-slate-200">
          {isSuccess && extractedData ? (
            <>
              {/* Toggle Raw/Formatted */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex gap-2">
                  <button
                    onClick={() => setShowRaw(false)}
                    className={clsx(
                      'px-3 py-1 text-sm rounded-lg transition-colors',
                      !showRaw
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-slate-600 hover:bg-slate-100'
                    )}
                  >
                    Formatted
                  </button>
                  <button
                    onClick={() => setShowRaw(true)}
                    className={clsx(
                      'px-3 py-1 text-sm rounded-lg transition-colors',
                      showRaw
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-slate-600 hover:bg-slate-100'
                    )}
                  >
                    Raw JSON
                  </button>
                </div>
                <button
                  onClick={handleDownloadJson}
                  className="flex items-center gap-1 text-sm text-slate-600 hover:text-slate-900"
                >
                  <Download className="w-4 h-4" />
                  Download
                </button>
              </div>

              {showRaw ? (
                <JsonViewer data={result.extracted_data} />
              ) : (
                <div className="space-y-4">
                  {/* Invoice Header - Key Information */}
                  <div className="bg-blue-50 rounded-lg p-4">
                    <h4 className="font-medium text-blue-900 mb-3">Invoice Details</h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div>
                        <p className="text-xs text-blue-600 mb-1">Invoice #</p>
                        <p className="font-semibold text-slate-900">
                          {extractedData.invoice_number || '—'}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-blue-600 mb-1">Invoice Date</p>
                        <p className="font-medium text-slate-900">
                          {extractedData.invoice_date || '—'}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-blue-600 mb-1">Due Date</p>
                        <p className="font-medium text-slate-900">
                          {extractedData.due_date || '—'}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-blue-600 mb-1">Currency</p>
                        <p className="font-medium text-slate-900">
                          {extractedData.currency || 'USD'}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Vendor & Customer Info */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Vendor/From */}
                    <div className="bg-slate-50 rounded-lg p-4">
                      <h4 className="font-medium text-slate-700 mb-2 flex items-center gap-2">
                        <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                        From (Vendor)
                      </h4>
                      <div className="space-y-2">
                        <p className="font-semibold text-slate-900">
                          {extractedData.vendor_name || '—'}
                        </p>
                        {extractedData.vendor_address && (
                          <p className="text-sm text-slate-600">
                            {extractedData.vendor_address}
                          </p>
                        )}
                        {extractedData.vendor_email && (
                          <p className="text-sm text-slate-600">
                            ✉ {extractedData.vendor_email}
                          </p>
                        )}
                        {extractedData.vendor_phone && (
                          <p className="text-sm text-slate-600">
                            ☎ {extractedData.vendor_phone}
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Customer/Bill To */}
                    <div className="bg-slate-50 rounded-lg p-4">
                      <h4 className="font-medium text-slate-700 mb-2 flex items-center gap-2">
                        <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                        Bill To (Customer)
                      </h4>
                      <div className="space-y-2">
                        <p className="font-semibold text-slate-900">
                          {extractedData.customer_name || extractedData.bill_to || '—'}
                        </p>
                        {extractedData.customer_address && (
                          <p className="text-sm text-slate-600">
                            {extractedData.customer_address}
                          </p>
                        )}
                        {extractedData.customer_email && (
                          <p className="text-sm text-slate-600">
                            ✉ {extractedData.customer_email}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Line Items */}
                  {extractedData.line_items && extractedData.line_items.length > 0 && (
                    <div className="mt-4">
                      <p className="text-sm font-medium text-slate-700 mb-2">
                        Line Items ({extractedData.line_items.length})
                      </p>
                      <div className="bg-slate-50 rounded-lg overflow-hidden">
                        <table className="w-full text-sm">
                          <thead className="bg-slate-100">
                            <tr>
                              <th className="text-left p-2 text-slate-600">Description</th>
                              <th className="text-right p-2 text-slate-600">Qty</th>
                              <th className="text-right p-2 text-slate-600">Unit Price</th>
                              <th className="text-right p-2 text-slate-600">Amount</th>
                            </tr>
                          </thead>
                          <tbody>
                            {extractedData.line_items.slice(0, 5).map((item, i) => (
                              <tr key={i} className="border-t border-slate-200">
                                <td className="p-2 text-slate-900 truncate max-w-[200px]">
                                  {item.description || '—'}
                                </td>
                                <td className="p-2 text-right text-slate-700">
                                  {item.quantity ?? '—'}
                                </td>
                                <td className="p-2 text-right text-slate-700">
                                  {safeToFixed(item.unit_price ?? item.price)}
                                </td>
                                <td className="p-2 text-right font-medium text-slate-900">
                                  {safeToFixed(item.amount)}
                                </td>
                              </tr>
                            ))}
                            {extractedData.line_items.length > 5 && (
                              <tr className="border-t border-slate-200">
                                <td colSpan={4} className="p-2 text-center text-slate-500 italic">
                                  ... and {extractedData.line_items.length - 5} more items
                                </td>
                              </tr>
                            )}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Totals Section */}
                  <div className="bg-green-50 rounded-lg p-4">
                    <h4 className="font-medium text-green-900 mb-3">Amounts ({extractedData.currency || 'USD'})</h4>
                    <div className="flex justify-end">
                      <div className="w-64 space-y-2">
                        {extractedData.subtotal != null && (
                          <div className="flex justify-between text-sm">
                            <span className="text-slate-600">Subtotal</span>
                            <span className="font-medium">{safeToFixed(extractedData.subtotal)}</span>
                          </div>
                        )}
                        {extractedData.discount_amount != null && extractedData.discount_amount > 0 && (
                          <div className="flex justify-between text-sm">
                            <span className="text-slate-600">Discount</span>
                            <span className="font-medium text-red-600">-{safeToFixed(extractedData.discount_amount)}</span>
                          </div>
                        )}
                        {extractedData.tax_amount != null && (
                          <div className="flex justify-between text-sm">
                            <span className="text-slate-600">Tax</span>
                            <span className="font-medium">{safeToFixed(extractedData.tax_amount)}</span>
                          </div>
                        )}
                        {extractedData.shipping_amount != null && extractedData.shipping_amount > 0 && (
                          <div className="flex justify-between text-sm">
                            <span className="text-slate-600">Shipping</span>
                            <span className="font-medium">{safeToFixed(extractedData.shipping_amount)}</span>
                          </div>
                        )}
                        <div className="flex justify-between font-bold text-lg border-t border-green-200 pt-2 mt-2">
                          <span className="text-green-800">Total</span>
                          <span className="text-green-600">
                            {extractedData.currency || ''} {safeToFixed(extractedData.total_amount)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Confidence */}
                  {result.validation && (
                    <div className="pt-2 border-t">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-slate-600">Extraction Confidence</span>
                        <ConfidenceIndicator score={result.validation.overall_score ?? 0} size="sm" />
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-4 text-red-600">
              <XCircle className="w-8 h-8 mx-auto mb-2" />
              <p className="font-medium">Extraction Failed</p>
              <p className="text-sm text-red-500 mt-1">
                {result.error?.message || 'Unknown error occurred'}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function BatchResultsPanel({ batchResult }: BatchResultsPanelProps) {
  const handleDownloadAll = () => {
    const blob = new Blob([JSON.stringify(batchResult, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `batch_extraction_${batchResult.batch_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
      {/* Summary Header */}
      <div className="px-6 py-4 border-b border-slate-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
              <Files className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h2 className="font-semibold text-slate-900">Batch Extraction Complete</h2>
              <p className="text-sm text-slate-500">
                {batchResult.total_files} file{batchResult.total_files > 1 ? 's' : ''} processed
              </p>
            </div>
          </div>
          <button
            onClick={handleDownloadAll}
            className="flex items-center gap-2 px-3 py-1.5 text-sm text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <Download className="w-4 h-4" />
            Download All
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="px-6 py-4 bg-slate-50 border-b border-slate-200">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
              <CheckCircle className="w-4 h-4 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-green-600">{batchResult.successful}</p>
              <p className="text-xs text-slate-500">Successful</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
              <XCircle className="w-4 h-4 text-red-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-red-600">{batchResult.failed}</p>
              <p className="text-xs text-slate-500">Failed</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-slate-100 rounded-full flex items-center justify-center">
              <FileText className="w-4 h-4 text-slate-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{batchResult.total_files}</p>
              <p className="text-xs text-slate-500">Total Files</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-slate-100 rounded-full flex items-center justify-center">
              <Clock className="w-4 h-4 text-slate-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">
                {safeToFixed(batchResult.total_time)}s
              </p>
              <p className="text-xs text-slate-500">Total Time</p>
            </div>
          </div>
        </div>
      </div>

      {/* Individual Results */}
      <div className="p-6 space-y-4">
        <h3 className="font-medium text-slate-900">Individual Results</h3>
        {batchResult.results.map((result, index) => (
          <SingleResultCard key={result.request_id} result={result} index={index} />
        ))}
      </div>
    </div>
  );
}
