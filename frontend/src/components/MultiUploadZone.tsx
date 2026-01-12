import { useState, useRef, useCallback } from 'react';
import { Upload, FileText, X, AlertCircle, Files } from 'lucide-react';
import clsx from 'clsx';

interface MultiUploadZoneProps {
  onFilesSelect: (files: File[]) => void;
  disabled?: boolean;
  maxSizeMb?: number;
  maxFiles?: number;
  acceptedFormats?: string[];
}

export function MultiUploadZone({
  onFilesSelect,
  disabled = false,
  maxSizeMb = 50,
  maxFiles = 5,
  acceptedFormats = ['.pdf'],
}: MultiUploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateFile = useCallback(
    (file: File): string | null => {
      if (!file) return 'No file provided';

      const ext = '.' + (file.name.split('.').pop()?.toLowerCase() || '');
      if (!acceptedFormats.includes(ext)) {
        return `Invalid file type: ${file.name}. Only PDF files accepted.`;
      }

      const sizeMb = file.size / (1024 * 1024);
      if (sizeMb > maxSizeMb) {
        return `File too large: ${file.name}. Maximum size: ${maxSizeMb}MB`;
      }

      return null;
    },
    [acceptedFormats, maxSizeMb]
  );

  const handleFiles = useCallback(
    (fileList: FileList | File[]) => {
      const files = Array.from(fileList);

      // Check max files
      if (files.length > maxFiles) {
        setError(`Too many files. Maximum ${maxFiles} files allowed.`);
        return;
      }

      // Validate each file
      for (const file of files) {
        const validationError = validateFile(file);
        if (validationError) {
          setError(validationError);
          return;
        }
      }

      setError(null);
      setSelectedFiles(files);

      try {
        onFilesSelect(files);
      } catch (err) {
        console.error('[MultiUploadZone] Error calling onFilesSelect:', err);
        setError('Failed to process files. Please try again.');
      }
    },
    [validateFile, onFilesSelect, maxFiles]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) {
      setIsDragging(true);
    }
  }, [disabled]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);

      if (disabled) return;

      const files = e.dataTransfer?.files;
      if (files && files.length > 0) {
        handleFiles(files);
      }
    },
    [disabled, handleFiles]
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        handleFiles(files);
      }
      if (inputRef.current) {
        inputRef.current.value = '';
      }
    },
    [handleFiles]
  );

  const handleClick = useCallback(() => {
    if (!disabled && inputRef.current) {
      inputRef.current.click();
    }
  }, [disabled]);

  const removeFile = useCallback((index: number, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setSelectedFiles(prev => {
      const newFiles = prev.filter((_, i) => i !== index);
      if (newFiles.length === 0) {
        setError(null);
      }
      return newFiles;
    });
  }, []);

  const clearSelection = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setSelectedFiles([]);
    setError(null);
    if (inputRef.current) {
      inputRef.current.value = '';
    }
  }, []);

  const formatFileSize = (bytes: number): string => {
    if (!bytes || isNaN(bytes)) return '0 B';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  const totalSize = selectedFiles.reduce((acc, file) => acc + file.size, 0);

  return (
    <div className="w-full">
      <div
        onClick={handleClick}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={clsx(
          'relative border-2 border-dashed rounded-xl p-8 transition-all duration-200 cursor-pointer',
          'flex flex-col items-center justify-center min-h-[200px]',
          {
            'border-blue-400 bg-blue-50': isDragging,
            'border-slate-300 bg-white hover:border-blue-400 hover:bg-slate-50': !isDragging && !disabled && !error,
            'border-red-300 bg-red-50': error,
            'border-slate-200 bg-slate-100 cursor-not-allowed opacity-60': disabled,
          }
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept={acceptedFormats.join(',')}
          onChange={handleInputChange}
          disabled={disabled}
          multiple
          className="hidden"
        />

        {selectedFiles.length > 0 ? (
          <div className="w-full space-y-3">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Files className="w-5 h-5 text-blue-600" />
                <span className="font-medium text-slate-900">
                  {selectedFiles.length} file{selectedFiles.length > 1 ? 's' : ''} selected
                </span>
                <span className="text-sm text-slate-500">
                  ({formatFileSize(totalSize)} total)
                </span>
              </div>
              <button
                onClick={clearSelection}
                className="text-sm text-red-600 hover:text-red-700 hover:underline"
              >
                Clear all
              </button>
            </div>

            <div className="space-y-2 max-h-[200px] overflow-y-auto">
              {selectedFiles.map((file, index) => (
                <div
                  key={`${file.name}-${index}`}
                  className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg"
                >
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <FileText className="w-5 h-5 text-blue-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-slate-900 truncate">
                      {file.name}
                    </p>
                    <p className="text-sm text-slate-500">
                      {formatFileSize(file.size)}
                    </p>
                  </div>
                  <button
                    onClick={(e) => removeFile(index, e)}
                    className="p-1 hover:bg-slate-200 rounded-full transition-colors flex-shrink-0"
                  >
                    <X className="w-4 h-4 text-slate-500" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <>
            <div
              className={clsx(
                'w-16 h-16 rounded-full flex items-center justify-center mb-4',
                isDragging ? 'bg-blue-100' : 'bg-slate-100'
              )}
            >
              <Upload
                className={clsx(
                  'w-8 h-8',
                  isDragging ? 'text-blue-600' : 'text-slate-400'
                )}
              />
            </div>
            <p className="text-slate-700 font-medium mb-1">
              {isDragging ? 'Drop your PDF(s) here' : 'Drag & drop your PDF(s) here'}
            </p>
            <p className="text-slate-500 text-sm">
              or <span className="text-blue-600 hover:underline">browse files</span>
            </p>
            <p className="text-slate-400 text-xs mt-2">
              Up to {maxFiles} files • Maximum {maxSizeMb}MB each
            </p>
          </>
        )}
      </div>

      {error && (
        <div className="mt-3 flex items-center gap-2 text-red-600 text-sm">
          <AlertCircle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
