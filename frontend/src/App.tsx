import { useState, useCallback, useEffect, useRef } from 'react';
import { Header } from './components/Header';
import { MultiUploadZone } from './components/MultiUploadZone';
import { ProgressBar } from './components/ProgressBar';
import { ResultsPanel } from './components/ResultsPanel';
import { BatchResultsPanel } from './components/BatchResultsPanel';
import { ErrorBoundary } from './components/ErrorBoundary';
import { ResumeAnalyzer } from './components/ResumeAnalyzer';
import { extractFromPdf, extractFromPdfBatch } from './services/api';
import type { UploadState, ExtractionResponse, BatchExtractionResponse } from './types';
import { AlertCircle, RotateCcw, FileText, Users, Sparkles, Zap, Brain, ArrowRight, ChevronRight } from 'lucide-react';

type TabType = 'landing' | 'extractor' | 'resume';

function App() {
  const [activeTab, setActiveTab] = useState<TabType>('landing');
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
    <div className="min-h-screen bg-slate-50 dark:bg-gray-900 flex flex-col">
      <Header />

      {/* Landing Page */}
      {activeTab === 'landing' && (
        <LandingPage onNavigate={setActiveTab} />
      )}

      {/* App Content (Extractor or Resume Analyzer) */}
      {activeTab !== 'landing' && (
        <>
          {/* Tab Navigation */}
          <div className="max-w-5xl mx-auto px-4 pt-6 w-full">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setActiveTab('landing')}
                className="text-slate-500 dark:text-gray-400 hover:text-slate-700 dark:hover:text-gray-200 transition-colors"
                title="Back to Home"
              >
                <ChevronRight className="w-5 h-5 rotate-180" />
              </button>
              <div className="flex-1 flex space-x-1 bg-slate-200 dark:bg-gray-800 p-1 rounded-lg">
                <button
                  onClick={() => setActiveTab('extractor')}
                  className={`
                    flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-md font-medium text-sm
                    transition-all duration-200
                    ${activeTab === 'extractor'
                      ? 'bg-white dark:bg-gray-700 text-slate-900 dark:text-gray-100 shadow-sm'
                      : 'text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-gray-200'
                    }
                  `}
                >
                  <FileText className="w-4 h-4" />
                  PDF Extractor
                </button>
                <button
                  onClick={() => setActiveTab('resume')}
                  className={`
                    flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-md font-medium text-sm
                    transition-all duration-200
                    ${activeTab === 'resume'
                      ? 'bg-white dark:bg-gray-700 text-slate-900 dark:text-gray-100 shadow-sm'
                      : 'text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-gray-200'
                    }
                  `}
                >
                  <Users className="w-4 h-4" />
                  Resume Analyzer
                </button>
              </div>
            </div>
          </div>

          <main className="max-w-5xl mx-auto px-4 py-8 w-full flex-1">
        {/* Resume Analyzer Tab */}
        {activeTab === 'resume' && (
          <ResumeAnalyzer />
        )}

        {/* PDF Extractor Tab */}
        {activeTab === 'extractor' && (
          <>
            {/* Upload Section */}
            <section className="mb-8">
              <div className="text-center mb-6">
                <h2 className="text-2xl font-bold text-slate-900 dark:text-gray-100 mb-2">
                  Extract Data from Your PDFs
                </h2>
                <p className="text-slate-600 dark:text-gray-400">
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
                <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                  <div className="flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-red-500 mt-0.5" />
                    <div className="flex-1">
                      <h3 className="font-medium text-red-800 dark:text-red-400">Extraction Failed</h3>
                      <p className="text-sm text-red-600 dark:text-red-500 mt-1">{uploadState.error}</p>
                    </div>
                    <button
                      onClick={handleReset}
                      className="flex items-center gap-1 px-3 py-1.5 text-sm bg-white dark:bg-gray-800 border border-red-200 dark:border-red-700 text-red-600 dark:text-red-400 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
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
                  <h3 className="text-lg font-semibold text-slate-900 dark:text-gray-100">
                    Extraction Results
                  </h3>
                  <button
                    onClick={handleReset}
                    className="flex items-center gap-1 px-3 py-1.5 text-sm text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-gray-200 hover:bg-slate-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
                  >
                    <RotateCcw className="w-4 h-4" />
                    Extract More
                  </button>
                </div>
                <ErrorBoundary
                  fallback={
                    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-red-200 dark:border-red-800 p-6">
                      <div className="text-center">
                        <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-3" />
                        <h3 className="font-medium text-red-800 dark:text-red-400 mb-2">Failed to render results</h3>
                        <p className="text-sm text-red-600 dark:text-red-500 mb-4">There was an error displaying the extraction results.</p>
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
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-gray-700 mt-auto">
        <div className="max-w-5xl mx-auto px-4 py-6 text-center text-sm text-slate-500 dark:text-gray-400">
          PDF Intelligence Extractor • Powered by Groq Cloud AI (LLaMA 3.3 70B)
        </div>
      </footer>
        </>
      )}
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
    <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-slate-200 dark:border-gray-700 text-center">
      <div className="text-4xl mb-3">{icon}</div>
      <h3 className="font-semibold text-slate-900 dark:text-gray-100 mb-1">{title}</h3>
      <p className="text-sm text-slate-500 dark:text-gray-400">{description}</p>
    </div>
  );
}

// Landing Page Component with animated hero and feature cards
function LandingPage({ onNavigate }: { onNavigate: (tab: TabType) => void }) {
  return (
    <div className="flex-1 flex flex-col">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        {/* Animated Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/10 via-blue-500/5 to-purple-500/10 dark:from-cyan-500/5 dark:via-blue-500/5 dark:to-purple-500/5" />
        <div className="absolute inset-0">
          <div className="absolute top-20 left-10 w-72 h-72 bg-cyan-400/20 rounded-full blur-3xl animate-pulse" />
          <div className="absolute top-40 right-20 w-96 h-96 bg-blue-400/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
          <div className="absolute bottom-10 left-1/3 w-64 h-64 bg-purple-400/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }} />
        </div>

        {/* Floating particles */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          {[...Array(20)].map((_, i) => (
            <div
              key={i}
              className="absolute w-1 h-1 bg-cyan-500/40 rounded-full animate-float"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 5}s`,
                animationDuration: `${3 + Math.random() * 4}s`,
              }}
            />
          ))}
        </div>

        <div className="relative max-w-6xl mx-auto px-4 py-20 md:py-32">
          {/* Badge */}
          <div className="flex justify-center mb-6 animate-fade-in">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm border border-slate-200 dark:border-gray-700 shadow-sm">
              <Sparkles className="w-4 h-4 text-amber-500" />
              <span className="text-sm font-medium text-slate-700 dark:text-gray-300">Powered by Groq Cloud AI</span>
            </div>
          </div>

          {/* Main Title */}
          <h1 className="text-4xl md:text-6xl font-bold text-center mb-6 animate-fade-in-up">
            <span className="bg-gradient-to-r from-slate-900 via-slate-700 to-slate-900 dark:from-white dark:via-gray-300 dark:to-white bg-clip-text text-transparent">
              PDF Intelligence
            </span>
            <br />
            <span className="bg-gradient-to-r from-cyan-500 via-blue-500 to-purple-500 bg-clip-text text-transparent">
              Extractor
            </span>
          </h1>

          {/* Subtitle */}
          <p className="text-lg md:text-xl text-slate-600 dark:text-gray-400 text-center max-w-2xl mx-auto mb-10 animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
            Transform your PDFs into structured data with the power of <span className="font-semibold text-cyan-600 dark:text-cyan-400">LLaMA 3.3 70B</span>.
            Extract invoices, analyze resumes, and rank candidates — all in seconds.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center animate-fade-in-up" style={{ animationDelay: '0.4s' }}>
            <button
              onClick={() => onNavigate('extractor')}
              className="group relative inline-flex items-center justify-center gap-2 px-8 py-4 bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-semibold rounded-xl shadow-lg shadow-cyan-500/25 hover:shadow-cyan-500/40 hover:scale-105 transition-all duration-300"
            >
              <FileText className="w-5 h-5" />
              <span>Extract from PDFs</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>
            <button
              onClick={() => onNavigate('resume')}
              className="group relative inline-flex items-center justify-center gap-2 px-8 py-4 bg-white dark:bg-gray-800 text-slate-900 dark:text-white font-semibold rounded-xl border-2 border-slate-200 dark:border-gray-700 hover:border-purple-400 dark:hover:border-purple-500 hover:shadow-lg hover:scale-105 transition-all duration-300"
            >
              <Users className="w-5 h-5" />
              <span>Analyze Resumes</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-4 bg-white dark:bg-gray-800/50">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 dark:text-white mb-4">
              What Can You Do?
            </h2>
            <p className="text-slate-600 dark:text-gray-400 max-w-2xl mx-auto">
              Two powerful tools designed for modern document processing
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {/* Invoice Extractor Card */}
            <div
              onClick={() => onNavigate('extractor')}
              className="group relative bg-gradient-to-br from-white to-slate-50 dark:from-gray-800 dark:to-gray-900 rounded-2xl p-8 border border-slate-200 dark:border-gray-700 hover:border-cyan-400 dark:hover:border-cyan-500 shadow-sm hover:shadow-xl cursor-pointer transition-all duration-300 hover:-translate-y-1"
            >
              <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-cyan-500/10 to-blue-500/10 rounded-full blur-2xl opacity-0 group-hover:opacity-100 transition-opacity" />

              <div className="relative">
                <div className="w-14 h-14 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-xl flex items-center justify-center mb-6 shadow-lg shadow-cyan-500/20 group-hover:scale-110 transition-transform">
                  <FileText className="w-7 h-7 text-white" />
                </div>

                <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-3">
                  Invoice Extractor
                </h3>

                <p className="text-slate-600 dark:text-gray-400 mb-6 leading-relaxed">
                  Upload invoices and instantly extract vendor details, line items, amounts, dates, and more into structured JSON format.
                </p>

                <ul className="space-y-3 mb-6">
                  {['Batch processing up to 5 files', 'Auto-detects document type', 'High accuracy extraction', 'Export to JSON'].map((item, i) => (
                    <li key={i} className="flex items-center gap-2 text-sm text-slate-600 dark:text-gray-400">
                      <div className="w-5 h-5 rounded-full bg-cyan-100 dark:bg-cyan-900/30 flex items-center justify-center">
                        <Zap className="w-3 h-3 text-cyan-600 dark:text-cyan-400" />
                      </div>
                      {item}
                    </li>
                  ))}
                </ul>

                <div className="flex items-center gap-2 text-cyan-600 dark:text-cyan-400 font-medium group-hover:gap-3 transition-all">
                  <span>Start Extracting</span>
                  <ArrowRight className="w-4 h-4" />
                </div>
              </div>
            </div>

            {/* Resume Analyzer Card */}
            <div
              onClick={() => onNavigate('resume')}
              className="group relative bg-gradient-to-br from-white to-slate-50 dark:from-gray-800 dark:to-gray-900 rounded-2xl p-8 border border-slate-200 dark:border-gray-700 hover:border-purple-400 dark:hover:border-purple-500 shadow-sm hover:shadow-xl cursor-pointer transition-all duration-300 hover:-translate-y-1"
            >
              <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-full blur-2xl opacity-0 group-hover:opacity-100 transition-opacity" />

              <div className="relative">
                <div className="w-14 h-14 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl flex items-center justify-center mb-6 shadow-lg shadow-purple-500/20 group-hover:scale-110 transition-transform">
                  <Users className="w-7 h-7 text-white" />
                </div>

                <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-3">
                  Resume Analyzer
                </h3>

                <p className="text-slate-600 dark:text-gray-400 mb-6 leading-relaxed">
                  Match candidates to job descriptions with AI-powered scoring. Rank multiple resumes and identify the best fit instantly.
                </p>

                <ul className="space-y-3 mb-6">
                  {['ATS compatibility scoring', 'Multi-resume ranking', 'Skills gap analysis', 'Red flag detection'].map((item, i) => (
                    <li key={i} className="flex items-center gap-2 text-sm text-slate-600 dark:text-gray-400">
                      <div className="w-5 h-5 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
                        <Brain className="w-3 h-3 text-purple-600 dark:text-purple-400" />
                      </div>
                      {item}
                    </li>
                  ))}
                </ul>

                <div className="flex items-center gap-2 text-purple-600 dark:text-purple-400 font-medium group-hover:gap-3 transition-all">
                  <span>Analyze Resumes</span>
                  <ArrowRight className="w-4 h-4" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Tech Stack Section */}
      <section className="py-16 px-4 border-t border-slate-200 dark:border-gray-700">
        <div className="max-w-4xl mx-auto text-center">
          <h3 className="text-sm font-semibold text-slate-500 dark:text-gray-400 uppercase tracking-wider mb-6">
            Powered by cutting-edge technology
          </h3>
          <div className="flex flex-wrap items-center justify-center gap-8">
            {[
              { name: 'Groq Cloud', desc: 'Ultra-fast inference' },
              { name: 'LLaMA 3.3 70B', desc: 'State-of-the-art LLM' },
              { name: 'FastAPI', desc: 'High-performance backend' },
              { name: 'React', desc: 'Modern frontend' },
            ].map((tech, i) => (
              <div key={i} className="flex flex-col items-center">
                <span className="font-semibold text-slate-900 dark:text-white">{tech.name}</span>
                <span className="text-xs text-slate-500 dark:text-gray-400">{tech.desc}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-gray-700 mt-auto py-6">
        <div className="max-w-5xl mx-auto px-4 text-center text-sm text-slate-500 dark:text-gray-400">
          PDF Intelligence Extractor • Powered by Groq Cloud AI (LLaMA 3.3 70B)
        </div>
      </footer>
    </div>
  );
}

export default App;
