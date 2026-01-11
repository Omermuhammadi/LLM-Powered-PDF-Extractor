import { useState, useRef, useCallback } from 'react';
import { Upload, FileText, X, AlertCircle } from 'lucide-react';
import clsx from 'clsx';

interface UploadZoneProps {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
  maxSizeMb?: number;
  acceptedFormats?: string[];
}

export function UploadZone({
  onFileSelect,
  disabled = false,
  maxSizeMb = 10,
  acceptedFormats = ['.pdf'],
}: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateFile = useCallback(
    (file: File): string | null => {
      // Check file type
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!acceptedFormats.includes(ext)) {
        return `Invalid file type. Accepted formats: ${acceptedFormats.join(', ')}`;
      }

      // Check file size
      const sizeMb = file.size / (1024 * 1024);
      if (sizeMb > maxSizeMb) {
        return `File too large. Maximum size: ${maxSizeMb}MB`;
      }

      return null;
    },
    [acceptedFormats, maxSizeMb]
  );

  const handleFile = useCallback(
    (file: File) => {
      const validationError = validateFile(file);
      if (validationError) {
        setError(validationError);
        setSelectedFile(null);
        return;
      }

      setError(null);
      setSelectedFile(file);
      onFileSelect(file);
    },
    [validateFile, onFileSelect]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

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

      const files = e.dataTransfer.files;
      if (files.length > 0) {
        handleFile(files[0]);
      }
    },
    [disabled, handleFile]
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        handleFile(files[0]);
      }
    },
    [handleFile]
  );

  const handleClick = useCallback(() => {
    if (!disabled && inputRef.current) {
      inputRef.current.click();
    }
  }, [disabled]);

  const clearSelection = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedFile(null);
    setError(null);
    if (inputRef.current) {
      inputRef.current.value = '';
    }
  }, []);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

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
          className="hidden"
        />

        {selectedFile ? (
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <FileText className="w-6 h-6 text-blue-600" />
            </div>
            <div className="flex-1">
              <p className="font-medium text-slate-900 truncate max-w-xs">
                {selectedFile.name}
              </p>
              <p className="text-sm text-slate-500">
                {formatFileSize(selectedFile.size)}
              </p>
            </div>
            <button
              onClick={clearSelection}
              className="p-1 hover:bg-slate-200 rounded-full transition-colors"
            >
              <X className="w-5 h-5 text-slate-500" />
            </button>
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
              {isDragging ? 'Drop your PDF here' : 'Drag & drop your PDF here'}
            </p>
            <p className="text-slate-500 text-sm">
              or <span className="text-blue-600 hover:underline">browse files</span>
            </p>
            <p className="text-slate-400 text-xs mt-2">
              Maximum file size: {maxSizeMb}MB
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
