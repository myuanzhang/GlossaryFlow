/**
 * FileUpload Component
 *
 * Handles markdown file upload with validation
 */

import React, { useCallback, useRef, useImperativeHandle, forwardRef } from 'react';
import { Upload, message, type UploadProps } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import { useTranslationStore } from '../../stores/translationStore';
import type { FileUploadProps } from '../../types/ui';

const { Dragger } = Upload;

export interface FileUploadRef {
  triggerFileSelect: () => void;
  clearFile: () => void;
}

interface FileUploadComponentProps extends Omit<FileUploadProps, 'onFileSelect'> {
  onContentReady: (content: string) => void;
}

const FileUpload = forwardRef<FileUploadRef, FileUploadComponentProps>(({
  accept = '.md,.markdown',
  placeholder = '点击或拖拽Markdown文件到此区域上传',
  maxSize = 10 * 1024 * 1024, // 10MB default
  label,
  optional = false,
  onContentReady
}, ref) => {
  const {
    uploadedFile,
    setUploadedFile,
    setUploadedContent,
    addError,
    clearErrors,
    clearUpload
  } = useTranslationStore();

  const uploadRef = useRef<any>(null);

  // Expose methods via ref
  useImperativeHandle(ref, () => ({
    triggerFileSelect: () => {
      // Find the hidden file input in Dragger and trigger click
      const inputElement = uploadRef.current?.querySelector?.('input[type="file"]');
      if (inputElement) {
        inputElement.click();
      }
    },
    clearFile: () => {
      clearUpload();
    }
  }));

  // Validate file
  const validateFile = useCallback((file: File): boolean => {
    // Check file type
    const validTypes = ['.md', '.markdown', 'text/markdown', 'text/plain'];
    const fileName = file.name.toLowerCase();
    const fileType = file.type.toLowerCase();

    const isValidType = validTypes.some(type =>
      fileName.endsWith(type) || fileType.includes('markdown') || fileType.includes('text')
    );

    if (!isValidType) {
      addError('只支持上传Markdown文件 (.md, .markdown)');
      return false;
    }

    // Check file size
    if (file.size > maxSize) {
      addError(`文件大小不能超过 ${Math.round(maxSize / 1024 / 1024)}MB`);
      return false;
    }

    return true;
  }, [maxSize, addError]);

  // Handle file selection
  const handleFileSelect = useCallback((file: File) => {
    if (!validateFile(file)) {
      return false; // Prevent upload
    }

    clearErrors();
    setUploadedFile(file);

    // Read file content
    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result as string;
      setUploadedContent(content);
      onContentReady(content);
    };

    reader.onerror = () => {
      addError('文件读取失败，请重试');
      setUploadedFile(null);
      setUploadedContent('');
    };

    reader.readAsText(file);
    return false; // Prevent default upload behavior
  }, [validateFile, setUploadedFile, setUploadedContent, addError, clearErrors, onContentReady]);

  // Custom upload request (handled by our logic)
  const customRequest: UploadProps['customRequest'] = useCallback(({ file, onSuccess }) => {
    const fileObj = file as File;
    if (handleFileSelect(fileObj)) {
      onSuccess?.({});
    }
  }, [handleFileSelect]);

  // Handle before upload
  const beforeUpload: UploadProps['beforeUpload'] = useCallback((file) => {
    return handleFileSelect(file);
  }, [handleFileSelect]);

  return (
    <div className="file-upload" ref={uploadRef}>
      {label && (
        <div className="file-upload-label">
          {label}
          {optional && <span className="optional-text">（可选）</span>}
        </div>
      )}

      <Dragger
        name="file"
        accept={accept}
        beforeUpload={beforeUpload}
        customRequest={customRequest}
        showUploadList={false}
        multiple={false}
        className="file-upload-dragger"
      >
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">{placeholder}</p>
        <p className="ant-upload-hint">
          支持单个文件上传，文件格式：.md, .markdown
        </p>
      </Dragger>

      {uploadedFile && (
        <div className="file-upload-info">
          <div className="file-info-item">
            <span className="file-info-label">文件名：</span>
            <span className="file-info-value">{uploadedFile.name}</span>
          </div>
          <div className="file-info-item">
            <span className="file-info-label">文件大小：</span>
            <span className="file-info-value">
              {(uploadedFile.size / 1024).toFixed(2)} KB
            </span>
          </div>
          <div className="file-info-item">
            <span className="file-info-label">最后修改：</span>
            <span className="file-info-value">
              {new Date(uploadedFile.lastModified).toLocaleString()}
            </span>
          </div>
        </div>
      )}
    </div>
  );
});

FileUpload.displayName = 'FileUpload';

export default FileUpload;