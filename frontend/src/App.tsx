import { useState, useCallback } from 'react';
import { Header } from './components/Header';
import { UploadZone } from './components/UploadZone';
import { ProgressBar } from './components/ProgressBar';
import { ResultsPanel } from './components/ResultsPanel';
import { extractFromPdf } from './services/api';
import type { UploadState } from './types';
import { AlertCircle, RotateCcw } from 'lucide-react';

function App() {
  const [uploadState, setUploadState] = useState<UploadState>({
    file: null,
    progress: 0,
    status: 'idle',
  });

  const handleFileSelect = useCallback(async (file: File) => {
    setUploadState({
      file,
      progress: 0,
      status: 'uploading',
    });

    try {
      // Start extraction
      const result = await extractFromPdf(file, {
        validateOutput: true,
        onProgress: (progress) => {
          setUploadState((prev) => ({
            ...prev,
            progress,
            status: progress < 50 ? 'uploading' : 'processing',
          }));
        },
      });

      // Simulate processing progress after upload
      setUploadState((prev) => ({
        ...prev,
        progress: 75,
        status: 'processing',
      }));

      // Small delay to show processing state
      await new Promise((resolve) => setTimeout(resolve, 500));

      setUploadState({
        file,
        progress: 100,
        status: 'success',
        result,
      });
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'An unknown error occurred';

      // Try to extract more specific error from axios response
      let detailedError = errorMessage;
      if ((error as { response?: { data?: { detail?: string | { error?: string; message?: string } } } }).response?.data?.detail) {
        const detail = (error as { response: { data: { detail: string | { error?: string; message?: string } } } }).response.data.detail;
        if (typeof detail === 'string') {
          detailedError = detail;
        } else if (detail.message) {
          detailedError = detail.message;
        } else if (detail.error) {
          detailedError = detail.error;
        }
      }

      setUploadState({
        file,
        progress: 100,
        status: 'error',
        error: detailedError,
      });
    }
  }, []);

  const handleReset = useCallback(() => {
    setUploadState({
      file: null,
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
              Extract Data from Your PDF
            </h2>
            <p className="text-slate-600">
              Upload an invoice or document and let AI extract structured data automatically
            </p>
          </div>

          <UploadZone
            onFileSelect={handleFileSelect}
            disabled={isProcessing}
            maxSizeMb={10}
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
                    ? 'AI is extracting data from your document...'
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
        {uploadState.status === 'success' && uploadState.result && (
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
                Extract Another
              </button>
            </div>
            <ResultsPanel result={uploadState.result} />
          </section>
        )}

        {/* Info Section */}
        {uploadState.status === 'idle' && (
          <section className="mt-12">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <FeatureCard
                icon="📄"
                title="Upload PDF"
                description="Drag and drop or click to upload your invoice or document"
              />
              <FeatureCard
                icon="🤖"
                title="AI Extraction"
                description="Our AI analyzes and extracts structured data automatically"
              />
              <FeatureCard
                icon="✨"
                title="Get Results"
                description="Download extracted data as JSON or view formatted results"
              />
            </div>
          </section>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 mt-auto">
        <div className="max-w-5xl mx-auto px-4 py-6 text-center text-sm text-slate-500">
          PDF Intelligence Extractor • Powered by Local AI (Phi-3 Mini)
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
