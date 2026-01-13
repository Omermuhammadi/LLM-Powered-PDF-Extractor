import { useState, useCallback, useRef } from 'react';
import {
  FileText,
  Upload,
  X,
  Play,
  AlertCircle,
  Loader2,
  Users,
  Briefcase,
} from 'lucide-react';
import { rankResumes } from '../services/api';
import type { ResumeAnalyzerState } from '../types';
import { RankingResultsPanel } from './RankingResultsPanel';

const SAMPLE_JD = `Senior Data Scientist
======================

Company: TechVentures Pakistan
Location: Islamabad, Pakistan (Hybrid - 3 days on-site)
Job Type: Full-time

About Us:
TechVentures is a leading AI company building next-generation analytics solutions.

Role Overview:
We're looking for a Senior Data Scientist to lead our ML initiatives and drive data-driven decision making across the organization.

Requirements:
-----------
• 4+ years of experience in Data Science or Machine Learning
• Expert proficiency in Python (required)
• Strong experience with Pandas, NumPy, Scikit-learn
• Experience with Deep Learning frameworks (TensorFlow or PyTorch)
• Proficiency in SQL and database management
• Experience with data visualization (Power BI, Tableau, or similar)
• Bachelor's degree in Computer Science, Statistics, or related field

Nice to Have:
------------
• Master's degree in relevant field
• Experience with NLP and text processing
• Knowledge of cloud platforms (AWS, GCP, or Azure)
• Experience with Docker and containerization
• Familiarity with MLOps and model deployment
• Experience with Spark or big data technologies

Responsibilities:
----------------
• Design and implement machine learning models for business problems
• Lead data science projects from conception to deployment
• Mentor junior data scientists and analysts
• Collaborate with engineering teams on model deployment
• Present insights to stakeholders and leadership
• Stay current with latest ML/AI research and best practices`;

export function ResumeAnalyzer() {
  const [state, setState] = useState<ResumeAnalyzerState>({
    mode: 'idle',
    jobDescriptionText: '',
    resumeFiles: [],
    progress: 0,
  });

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFilesSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const pdfFiles = files.filter(f => f.name.toLowerCase().endsWith('.pdf'));

    if (pdfFiles.length > 0) {
      setState(prev => ({
        ...prev,
        resumeFiles: [...prev.resumeFiles, ...pdfFiles].slice(0, 10), // Max 10 files
      }));
    }

    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  const removeFile = useCallback((index: number) => {
    setState(prev => ({
      ...prev,
      resumeFiles: prev.resumeFiles.filter((_, i) => i !== index),
    }));
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files);
    const pdfFiles = files.filter(f => f.name.toLowerCase().endsWith('.pdf'));

    if (pdfFiles.length > 0) {
      setState(prev => ({
        ...prev,
        resumeFiles: [...prev.resumeFiles, ...pdfFiles].slice(0, 10),
      }));
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
  }, []);

  const loadSampleJD = useCallback(() => {
    setState(prev => ({
      ...prev,
      jobDescriptionText: SAMPLE_JD,
    }));
  }, []);

  const canAnalyze = state.jobDescriptionText.trim().length > 50 && state.resumeFiles.length > 0;

  const handleAnalyze = useCallback(async () => {
    if (!canAnalyze) return;

    setState(prev => ({
      ...prev,
      mode: 'uploading',
      progress: 0,
      error: undefined,
      rankingResult: undefined,
    }));

    try {
      // Start analysis
      setState(prev => ({ ...prev, mode: 'analyzing', progress: 30 }));

      const result = await rankResumes(
        state.resumeFiles,
        state.jobDescriptionText,
        {
          onProgress: (progress) => {
            setState(prev => ({ ...prev, progress: Math.min(progress, 30) }));
          },
        }
      );

      setState(prev => ({
        ...prev,
        mode: 'complete',
        progress: 100,
        rankingResult: result,
      }));

    } catch (error) {
      console.error('Analysis failed:', error);
      setState(prev => ({
        ...prev,
        mode: 'error',
        error: error instanceof Error ? error.message : 'Analysis failed',
      }));
    }
  }, [canAnalyze, state.resumeFiles, state.jobDescriptionText]);

  const handleReset = useCallback(() => {
    setState({
      mode: 'idle',
      jobDescriptionText: '',
      resumeFiles: [],
      progress: 0,
    });
  }, []);

  // Show results if analysis is complete
  if (state.mode === 'complete' && state.rankingResult) {
    return (
      <RankingResultsPanel
        result={state.rankingResult}
        onBack={handleReset}
      />
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8 text-center">
        <div className="flex items-center justify-center gap-3 mb-3">
          <Users className="w-8 h-8 text-blue-500" />
          <h1 className="text-3xl font-bold text-gray-800 dark:text-gray-100">
            Resume Analyzer
          </h1>
        </div>
        <p className="text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
          Upload multiple resumes and a job description to rank candidates,
          detect red flags, and get hiring recommendations.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Job Description */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-200 flex items-center gap-2">
              <Briefcase className="w-5 h-5" />
              Job Description
            </h2>
            <button
              onClick={loadSampleJD}
              className="text-sm text-blue-500 hover:text-blue-600 hover:underline"
            >
              Load Sample JD
            </button>
          </div>

          <textarea
            value={state.jobDescriptionText}
            onChange={(e) => setState(prev => ({ ...prev, jobDescriptionText: e.target.value }))}
            placeholder="Paste the job description here...&#10;&#10;Include requirements, responsibilities, and desired skills."
            className="w-full h-96 p-4 border border-gray-300 dark:border-gray-600 rounded-lg
                       bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200
                       focus:ring-2 focus:ring-blue-500 focus:border-transparent
                       resize-none font-mono text-sm"
            disabled={state.mode === 'analyzing' || state.mode === 'uploading'}
          />

          <div className="text-sm text-gray-500 dark:text-gray-400">
            {state.jobDescriptionText.length} characters
            {state.jobDescriptionText.length < 50 && (
              <span className="text-amber-500 ml-2">
                (minimum 50 characters required)
              </span>
            )}
          </div>
        </div>

        {/* Right: Resume Upload */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-200 flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Resumes ({state.resumeFiles.length}/10)
          </h2>

          {/* Drop Zone */}
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onClick={() => fileInputRef.current?.click()}
            className={`
              border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
              transition-all duration-200
              ${state.resumeFiles.length >= 10
                ? 'border-gray-300 bg-gray-50 dark:border-gray-600 dark:bg-gray-800 opacity-50 cursor-not-allowed'
                : 'border-blue-300 dark:border-blue-600 hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20'
              }
            `}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf"
              onChange={handleFilesSelect}
              className="hidden"
              disabled={state.resumeFiles.length >= 10 || state.mode === 'analyzing'}
            />
            <Upload className="w-10 h-10 mx-auto mb-3 text-blue-400" />
            <p className="text-gray-600 dark:text-gray-400">
              Drop PDF resumes here or <span className="text-blue-500">browse</span>
            </p>
            <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
              Maximum 10 files, PDF format only
            </p>
          </div>

          {/* File List */}
          {state.resumeFiles.length > 0 && (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {state.resumeFiles.map((file, index) => (
                <div
                  key={`${file.name}-${index}`}
                  className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800
                             rounded-lg border border-gray-200 dark:border-gray-700"
                >
                  <div className="flex items-center gap-3 overflow-hidden">
                    <FileText className="w-5 h-5 text-red-500 flex-shrink-0" />
                    <div className="overflow-hidden">
                      <p className="text-sm font-medium text-gray-700 dark:text-gray-300 truncate">
                        {file.name}
                      </p>
                      <p className="text-xs text-gray-400">
                        {(file.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFile(index);
                    }}
                    className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-full transition-colors"
                    disabled={state.mode === 'analyzing'}
                  >
                    <X className="w-4 h-4 text-gray-500" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Error Message */}
      {state.mode === 'error' && state.error && (
        <div className="mt-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
            <AlertCircle className="w-5 h-5" />
            <span className="font-medium">Analysis Failed</span>
          </div>
          <p className="mt-1 text-sm text-red-500 dark:text-red-400">{state.error}</p>
        </div>
      )}

      {/* Progress Bar */}
      {(state.mode === 'uploading' || state.mode === 'analyzing') && (
        <div className="mt-6">
          <div className="flex items-center gap-2 mb-2">
            <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {state.mode === 'uploading' ? 'Uploading resumes...' : 'Analyzing candidates...'}
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${state.progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Analyze Button */}
      <div className="mt-8 flex justify-center">
        <button
          onClick={handleAnalyze}
          disabled={!canAnalyze || state.mode === 'analyzing' || state.mode === 'uploading'}
          className={`
            flex items-center gap-2 px-8 py-3 rounded-lg font-semibold
            transition-all duration-200 text-lg
            ${canAnalyze && state.mode !== 'analyzing'
              ? 'bg-blue-500 hover:bg-blue-600 text-white shadow-lg hover:shadow-xl'
              : 'bg-gray-300 dark:bg-gray-700 text-gray-500 cursor-not-allowed'
            }
          `}
        >
          {state.mode === 'analyzing' || state.mode === 'uploading' ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <Play className="w-5 h-5" />
              Analyze & Rank Candidates
            </>
          )}
        </button>
      </div>

      {/* Instructions */}
      <div className="mt-8 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <h3 className="font-semibold text-blue-700 dark:text-blue-300 mb-2">
          How it works:
        </h3>
        <ul className="text-sm text-blue-600 dark:text-blue-400 space-y-1">
          <li>1. Paste or type your job description on the left</li>
          <li>2. Upload PDF resumes (up to 10) on the right</li>
          <li>3. Click "Analyze & Rank Candidates" to get results</li>
          <li>4. View ranked candidates with scores, red flags, and recommendations</li>
        </ul>
      </div>
    </div>
  );
}
