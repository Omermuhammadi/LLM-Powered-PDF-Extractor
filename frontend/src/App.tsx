import { useState, useCallback, useEffect, useRef } from 'react';
import { Header } from './components/Header';
import { MultiUploadZone } from './components/MultiUploadZone';
import { ProgressBar } from './components/ProgressBar';
import { ResultsPanel } from './components/ResultsPanel';
import { BatchResultsPanel } from './components/BatchResultsPanel';
import { ErrorBoundary } from './components/ErrorBoundary';
import { extractFromPdf, extractFromPdfBatch } from './services/api';
import type { UploadState, ExtractionResponse, BatchExtractionResponse } from './types';
import { AlertCircle, RotateCcw } from 'lucide-react';

function App() {
  const [uploadState, setUploadState] = useState<UploadState>({
    files: [],
    progress: 0,
    status: 'idle',
  });

  // Track if component is mounted to prevent state updates on unmounted component
  const isMounted = useRef(true);

  // Track current extraction request to prevent race conditions
  const currentRequestId = useRef<number>(0);

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  // Debug logging to track state changes
  useEffect(() => {
    console.log('[App] Upload state changed:', {
      status: uploadState.status,
      fileCount: uploadState.files.length,
      hasResult: !!uploadState.result,
      hasBatchResult: !!uploadState.batchResult,
      hasError: !!uploadState.error,
    });
  }, [uploadState]);

  const handleFilesSelect = useCallback(async (files: File[]) => {
    console.log('[App] Files selected:', files.map(f => f.name));

    // Increment request ID to track this specific request
    const requestId = ++currentRequestId.current;

    setUploadState({
      files,
      progress: 0,
      status: 'uploading',
    });

    try {
      // Start extraction
      console.log('[App] Starting extraction (request:', requestId, ')...');

      let result: ExtractionResponse | undefined;
      let batchResult: BatchExtractionResponse | undefined;

      if (files.length === 1) {
        // Single file - use regular endpoint for efficiency
        result = await extractFromPdf(files[0], {
          validateOutput: true,
          onProgress: (progress) => {
            if (currentRequestId.current === requestId && isMounted.current) {
              setUploadState((prev) => ({
                ...prev,
                progress,
                status: progress < 50 ? 'uploading' : 'processing',
              }));
            }
          },
        });
      } else {
        // Multiple files - use batch endpoint
        batchResult = await extractFromPdfBatch(files, {
          validateOutput: true,
          onProgress: (progress) => {
            if (currentRequestId.current === requestId && isMounted.current) {
              setUploadState((prev) => ({
                ...prev,
                progress,
                status: progress < 50 ? 'uploading' : 'processing',
              }));
            }
          },
        });
      }

      // Only process result if this is still the current request
      if (currentRequestId.current !== requestId || !isMounted.current) {
        console.log('[App] Request', requestId, 'was superseded, ignoring result');
        return;
      }

      console.log('[App] Extraction completed for request', requestId);

      // Simulate processing progress after upload
      setUploadState((prev) => ({
        ...prev,
        progress: 75,
        status: 'processing',
      }));

      // Small delay to show processing state
      await new Promise((resolve) => setTimeout(resolve, 300));

      // Final check before setting success state
      if (currentRequestId.current !== requestId || !isMounted.current) {
        return;
      }

      setUploadState({
        files,
        progress: 100,
        status: 'success',
        result,
        batchResult,
      });

      console.log('[App] State set to success for request', requestId);
    } catch (error) {
      // Only handle error if this is still the current request
      if (currentRequestId.current !== requestId || !isMounted.current) {
        console.log('[App] Request', requestId, 'error ignored (superseded)');
        return;
      }

      console.error('[App] Extraction error for request', requestId, ':', error);

      const errorMessage =
        error instanceof Error ? error.message : 'An unknown error occurred';

      // Try to extract more specific error from axios response
      let detailedError: string = errorMessage;
      const maybeResponse = (error as {
        response?: { data?: { detail?: unknown } };
      }).response;

      const detail = maybeResponse?.data?.detail as
        | string
        | {
            message?: string;
            error?: unknown;
          }
        | undefined;

      if (typeof detail === 'string') {
        detailedError = detail;
      } else if (detail && typeof detail === 'object') {
        if (typeof detail.message === 'string') {
          detailedError = detail.message;
        } else if (detail.error) {
          const err = detail.error as
            | string
            | { message?: string; code?: string };
          if (typeof err === 'string') {
            detailedError = err;
          } else if (err && typeof err === 'object') {
            detailedError =
              err.message || err.code || JSON.stringify(err);
          }
        }
      }

      setUploadState({
        files,
        progress: 100,
        status: 'error',
        error: detailedError,
      });
    }
  }, []);

  const handleReset = useCallback(() => {
    console.log('[App] Resetting state');
    setUploadState({
      files: [],
      progress: 0,
      status: 'idle',
    });
  }, []);

  const isProcessing =
    uploadState.status === 'uploading' || uploadState.status === 'processing';

  return (
    <div className="min-h-screen bg-slate-50">
      <Header />

      <main className="max-w-5xl mx-auto px-4 py-8">
        {/* Upload Section */}
        <section className="mb-8">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold text-slate-900 mb-2">
              Extract Data from Your PDFs
            </h2>
            <p className="text-slate-600">
              Upload up to 5 invoices and let AI extract structured data automatically
            </p>
          </div>

          <MultiUploadZone
            onFilesSelect={handleFilesSelect}
            disabled={isProcessing}
            maxSizeMb={50}
            maxFiles={5}
            acceptedFormats={['.pdf']}
          />

          {/* Progress */}
          {uploadState.status !== 'idle' && (
            <div className="mt-4">
              <ProgressBar
                progress={uploadState.progress}
                status={uploadState.status}
                statusText={
                  uploadState.status === 'processing'
                    ? `AI is extracting data from ${uploadState.files.length} file${uploadState.files.length > 1 ? 's' : ''}...`
                    : undefined
                }
              />
            </div>
          )}

          {/* Error State */}
          {uploadState.status === 'error' && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-500 mt-0.5" />
                <div className="flex-1">
                  <h3 className="font-medium text-red-800">Extraction Failed</h3>
                  <p className="text-sm text-red-600 mt-1">{uploadState.error}</p>
                </div>
                <button
                  onClick={handleReset}
                  className="flex items-center gap-1 px-3 py-1.5 text-sm bg-white border border-red-200 text-red-600 rounded-lg hover:bg-red-50 transition-colors"
                >
                  <RotateCcw className="w-4 h-4" />
                  Try Again
                </button>
              </div>
            </div>
          )}
        </section>

        {/* Results Section */}
        {uploadState.status === 'success' && (
          <section className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-slate-900">
                Extraction Results
              </h3>
              <button
                onClick={handleReset}
                className="flex items-center gap-1 px-3 py-1.5 text-sm text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
              >
                <RotateCcw className="w-4 h-4" />
                Extract More
              </button>
            </div>
            <ErrorBoundary
              fallback={
                <div className="bg-white rounded-xl shadow-sm border border-red-200 p-6">
                  <div className="text-center">
                    <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-3" />
                    <h3 className="font-medium text-red-800 mb-2">Failed to render results</h3>
                    <p className="text-sm text-red-600 mb-4">There was an error displaying the extraction results.</p>
                    <button
                      onClick={handleReset}
                      className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                    >
                      Try Again
                    </button>
                  </div>
                </div>
              }
            >
              {uploadState.batchResult ? (
                <BatchResultsPanel batchResult={uploadState.batchResult} />
              ) : uploadState.result ? (
                <ResultsPanel result={uploadState.result} />
              ) : null}
            </ErrorBoundary>
          </section>
        )}

        {/* Info Section */}
        {uploadState.status === 'idle' && (
          <section className="mt-12">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <FeatureCard
                icon="📄"
                title="Upload PDFs"
                description="Drag and drop up to 5 invoices at once"
              />
              <FeatureCard
                icon="🤖"
                title="AI Extraction"
                description="LLaMA 3.3 70B extracts data with high accuracy"
              />
              <FeatureCard
                icon="✨"
                title="Get Results"
                description="Download structured JSON or view formatted results"
              />
            </div>
          </section>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 mt-auto">
        <div className="max-w-5xl mx-auto px-4 py-6 text-center text-sm text-slate-500">
          PDF Intelligence Extractor • Powered by Groq Cloud AI (LLaMA 3.3 70B)
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: string;
  title: string;
  description: string;
}) {
  return (
    <div className="bg-white p-6 rounded-xl border border-slate-200 text-center">
      <div className="text-4xl mb-3">{icon}</div>
      <h3 className="font-semibold text-slate-900 mb-1">{title}</h3>
      <p className="text-sm text-slate-500">{description}</p>
    </div>
  );
}

export default App;
