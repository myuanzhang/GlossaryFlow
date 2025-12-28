/**
 * GlossaryUpload Component
 *
 * Handles glossary file upload with validation (JSON/YAML format)
 * This is an OPTIONAL feature - users can skip glossary upload
 */

import React, { useCallback, useRef, useImperativeHandle, forwardRef, useState } from 'react';
import './style.css';
import './enhanced.css';
import { Upload, message, Tag, Button, Space, type UploadProps } from 'antd';
import { BookOutlined, DeleteOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { useTranslationStore } from '../../stores/translationStore';
import type { GlossaryUploadProps, GlossaryUploadRef } from '../../types/ui';

const { Dragger } = Upload;

const GlossaryUpload = forwardRef<GlossaryUploadRef, GlossaryUploadProps>(({
  maxSize = 1 * 1024 * 1024, // 1MB default
  optional = true,
  onGlossaryReady
}, ref) => {
  const {
    glossaryFile,
    setGlossaryFile,
    setGlossaryData,
    clearGlossary
  } = useTranslationStore();

  const [glossaryPreview, setGlossaryPreview] = useState<Record<string, string> | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const uploadRef = useRef<any>(null);

  // Expose methods via ref
  useImperativeHandle(ref, () => ({
    clearGlossary: () => {
      clearGlossary();
      setGlossaryPreview(null);
    },
    getGlossary: () => glossaryPreview
  }));

  // Validate glossary file
  const validateGlossaryFile = useCallback((file: File): boolean => {
    // Check file extension
    const validExtensions = ['.json', '.yaml', '.yml'];
    const fileName = file.name.toLowerCase();
    const isValidExtension = validExtensions.some(ext => fileName.endsWith(ext));

    if (!isValidExtension) {
      message.warning(`术语表文件格式不支持：${file.name}，支持格式：.json, .yaml, .yml`);
      return false;
    }

    // Check file size
    if (file.size > maxSize) {
      message.warning(`术语表文件过大：${file.name}，最大支持 ${Math.round(maxSize / 1024 / 1024)}MB`);
      return false;
    }

    return true;
  }, [maxSize]);

  // Parse JSON glossary
  const parseJSONGlossary = useCallback((content: string): Record<string, string> => {
    try {
      const data = JSON.parse(content);

      // Validate format
      if (typeof data !== 'object' || data === null) {
        throw new Error('术语表格式错误：必须是对象');
      }

      // Check all keys and values are strings
      for (const [key, value] of Object.entries(data)) {
        if (typeof key !== 'string' || typeof value !== 'string') {
          throw new Error('术语表格式错误：所有键和值必须是字符串');
        }
      }

      return data;
    } catch (error) {
      if (error instanceof SyntaxError) {
        throw new Error('JSON 格式错误：文件内容不是有效的 JSON');
      }
      throw error;
    }
  }, []);

  // Handle file selection
  const handleFileSelect = useCallback(async (file: File) => {
    if (!validateGlossaryFile(file)) {
      return false; // Prevent upload
    }

    setIsLoading(true);

    try {
      // Read file content
      const content = await file.text();

      // Parse based on file extension
      const fileName = file.name.toLowerCase();
      let glossaryData: Record<string, string>;

      if (fileName.endsWith('.json')) {
        glossaryData = parseJSONGlossary(content);
      } else if (fileName.endsWith('.yaml') || fileName.endsWith('.yml')) {
        // TODO: Add YAML support in Phase 2
        message.warning('YAML 格式暂未支持，请使用 JSON 格式');
        setIsLoading(false);
        return false;
      } else {
        throw new Error('不支持的文件格式');
      }

      // Update state
      setGlossaryFile(file);
      setGlossaryData(glossaryData);
      setGlossaryPreview(glossaryData);

      // Notify parent component
      if (onGlossaryReady) {
        onGlossaryReady(glossaryData);
      }

      message.success(`术语表加载成功：${file.name}（包含 ${Object.keys(glossaryData).length} 个术语）`);

    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : '术语表文件解析失败';
      message.warning(`${errorMsg}，您可以跳过术语表继续翻译`);
      clearGlossary();
      setGlossaryPreview(null);
    } finally {
      setIsLoading(false);
    }

    return false; // Prevent default upload behavior
  }, [validateGlossaryFile, parseJSONGlossary, setGlossaryFile, setGlossaryData, clearGlossary, onGlossaryReady]);

  // Handle clear button
  const handleClear = useCallback(() => {
    clearGlossary();
    setGlossaryPreview(null);
    message.info('已清除术语表，您可以继续翻译（不使用术语表）');
  }, [clearGlossary]);

  // Custom upload request
  const customRequest: UploadProps['customRequest'] = useCallback(({ file, onSuccess }) => {
    const fileObj = file as File;
    handleFileSelect(fileObj).then((result) => {
      if (result !== false) {
        onSuccess?.({});
      }
    });
  }, [handleFileSelect]);

  // Handle before upload
  const beforeUpload: UploadProps['beforeUpload'] = useCallback((file) => {
    return handleFileSelect(file);
  }, [handleFileSelect]);

  // Get preview items (show first 3 terms)
  const getPreviewItems = () => {
    if (!glossaryPreview) return [];

    const entries = Object.entries(glossaryPreview).slice(0, 3);
    return entries.map(([chinese, english], index) => (
      <Tag key={index} color="blue" style={{ marginBottom: 4 }}>
        {chinese} → {english}
      </Tag>
    ));
  };

  return (
    <div className="glossary-upload">
      <Dragger
        ref={uploadRef}
        name="file"
        accept=".json,.yaml,.yml"
        beforeUpload={beforeUpload}
        customRequest={customRequest}
        showUploadList={false}
        multiple={false}
        disabled={isLoading}
      >
        <p className="ant-upload-drag-icon">
          <BookOutlined />
        </p>
        <p className="ant-upload-text">
          {optional ? '点击或拖拽术语表文件到此区域上传（可选）' : '点击或拖拽术语表文件到此区域上传'}
        </p>
        <p className="ant-upload-hint">
          支持 JSON、YAML 格式，文件大小不超过 {Math.round(maxSize / 1024 / 1024)}MB
          {optional && '，您可以跳过此步骤'}
        </p>
      </Dragger>

      {glossaryFile && glossaryPreview && (
        <div className="glossary-upload-info" style={{ marginTop: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <Space>
              <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 16 }} />
              <span style={{ fontWeight: 500 }}>已加载术语表：{glossaryFile.name}</span>
              <Tag color="success">{Object.keys(glossaryPreview).length} 个术语</Tag>
            </Space>
            <Button
              type="text"
              danger
              size="small"
              icon={<DeleteOutlined />}
              onClick={handleClear}
            >
              清除
            </Button>
          </div>

          {Object.keys(glossaryPreview).length > 0 && (
            <div style={{ marginTop: 8, padding: '8px 12px', background: '#f5f5f5', borderRadius: 4 }}>
              <div style={{ fontSize: 12, color: '#666', marginBottom: 4 }}>示例术语：</div>
              <Space size={[4, 4]} wrap>
                {getPreviewItems()}
                {Object.keys(glossaryPreview).length > 3 && (
                  <Tag style={{ borderStyle: 'dashed' }}>
                    +{Object.keys(glossaryPreview).length - 3} 更多
                  </Tag>
                )}
              </Space>
            </div>
          )}
        </div>
      )}

      {!glossaryFile && optional && (
        <div style={{ marginTop: 8, fontSize: 12, color: '#999' }}>
          提示：术语表可以帮助确保特定词汇翻译的一致性，未使用术语表也可以正常翻译
        </div>
      )}
    </div>
  );
});

GlossaryUpload.displayName = 'GlossaryUpload';

export default GlossaryUpload;
