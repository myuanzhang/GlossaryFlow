/**
 * DocumentUpload Page
 *
 * Main page for uploading documents and starting translation
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import {
  Layout,
  Typography,
  Button,
  Space,
  Card,
  Alert,
  Divider,
  message
} from 'antd';
import {
  FileTextOutlined,
  TranslationOutlined,
  RocketOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import { FileUpload, ProviderSelector, ErrorDisplay } from '../../components';
import GlossaryUpload from '../../components/GlossaryUpload';
import type { FileUploadRef } from '../../components/FileUpload';
import { useTranslationJob, useFileUpload, useNotifications, useProviderConfig, useTranslationStore, useGlossary } from '../../stores/translationStore';
import type { TranslationRequest } from '../../types/api';
import './style.css';

const { Header, Content } = Layout;
const { Title, Paragraph, Text } = Typography;

const DocumentUploadPage: React.FC = () => {
  const { startTranslation } = useTranslationJob();
  const { uploadedFile, clearUpload } = useFileUpload();
  const { clearErrors } = useNotifications();
  const { selectedProvider, selectedModel } = useProviderConfig();
  const { glossaryData } = useGlossary();

  const [isTranslating, setIsTranslating] = useState(false);
  const [fileContent, setFileContent] = useState('');
  const [shouldNavigate, setShouldNavigate] = useState(false);

  const fileUploadRef = useRef<FileUploadRef>(null);

  // Handle navigation when flag is set
  useEffect(() => {
    if (shouldNavigate) {
      console.log('🔄 Navigating to /progress due to flag change...');

      // Get current job ID from store before it's cleared
      const { currentJobId } = useTranslationStore.getState();

      if (currentJobId) {
        // Use window.location.href with job_id parameter
        // This ensures the job ID is preserved after page refresh
        window.location.href = `/progress?jobId=${currentJobId}`;
      } else {
        console.error('❌ No job ID available for navigation');
        message.error('无法获取任务ID，请重试');
      }

      setShouldNavigate(false);
    }
  }, [shouldNavigate]);

  // Handle file content ready
  const handleFileContentReady = useCallback((content: string) => {
    setFileContent(content);
    clearErrors();
  }, [clearErrors]);

  // Handle start translation
  const handleStartTranslation = async () => {
    if (!uploadedFile || !fileContent) {
      message.error('请先上传文件');
      return;
    }

    if (fileContent.trim().length === 0) {
      message.error('文件内容为空，请检查文件');
      return;
    }

    if (!selectedProvider || !selectedModel) {
      message.error('请先选择翻译服务商和模型');
      return;
    }

    setIsTranslating(true);

    try {
      // Create translation request with provider and model info
      const request: TranslationRequest = {
        source_markdown: fileContent,
        glossary: glossaryData || undefined, // Optional: only include if glossary data exists
        llm_config: {
          provider: selectedProvider as "openai" | "ollama" | "mimo" | "deepseek" | "qwen",
          model: selectedModel,
          temperature: 0.3
        }
      };

      console.log('🚀 Starting translation request...');
      const startTime = Date.now();

      // Start translation
      const response = await startTranslation(request);

      const elapsed = Date.now() - startTime;
      console.log(`✅ Translation started in ${elapsed}ms, job ID: ${response.job_id}`);

      // ⚠️ CRITICAL: Failure First - 只有成功且有 job_id 时才跳转
      if (response && response.job_id) {
        message.success('翻译已开始，正在跳转到进度页面...');
        setShouldNavigate(true);
      } else {
        // 异常情况：有响应但无 job_id
        message.error('翻译启动异常：未获取到任务ID');
        console.error('❌ Translation response missing job_id:', response);
      }

    } catch (error) {
      // ❌ 失败：显示错误，停留在当前页面，不跳转
      const errorMessage = error instanceof Error ? error.message : '翻译启动失败';
      console.error('❌ Failed to start translation:', errorMessage);

      // 显示详细错误信息
      message.error({
        content: errorMessage,
        duration: 5, // 显示更长时间以便用户阅读
        key: 'translation-start-error'
      });
    } finally {
      setIsTranslating(false);
    }
  };

  // Handle reset
  const handleReset = () => {
    clearUpload();
    setFileContent('');
    clearErrors();
    // Trigger file selection dialog after clearing state
    fileUploadRef.current?.triggerFileSelect();
  };

  // Check if can start translation
  const canStartTranslation = uploadedFile && fileContent.trim().length > 0 && !isTranslating;

  return (
    <Layout className="document-upload-page">
      <Header className="page-header">
        <div className="header-content">
          <Space size="large">
            <TranslationOutlined className="page-icon" />
            <div>
              <Title level={2} className="page-title">
                文档翻译
              </Title>
              <Text className="page-subtitle">
                上传Markdown文件，选择翻译服务商，开始智能翻译
              </Text>
            </div>
          </Space>
        </div>
      </Header>

      <Content className="page-content">
        <div className="content-wrapper">
          {/* Introduction Card */}
          <Card className="intro-card" bordered={false}>
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              <div className="intro-header">
                <Space>
                  <FileTextOutlined style={{ fontSize: 24, color: '#1890ff' }} />
                  <Title level={3} style={{ margin: 0 }}>
                    智能文档翻译
                  </Title>
                </Space>
              </div>

              <div className="intro-content">
                <Paragraph>
                  使用先进的AI翻译技术，将您的中文Markdown文档精准翻译为英文。
                  系统会自动保留文档格式、代码块和链接结构。
                </Paragraph>

                <div className="features-list">
                  <Space direction="vertical" size="small">
                    <div className="feature-item">
                      <InfoCircleOutlined className="feature-icon" />
                      <Text>保留原始Markdown格式和结构</Text>
                    </div>
                    <div className="feature-item">
                      <InfoCircleOutlined className="feature-icon" />
                      <Text>不翻译代码块、链接和文件路径</Text>
                    </div>
                    {/* <div className="feature-item">
                      <InfoCircleOutlined className="feature-icon" />
                      <Text>实时进度跟踪，支持WebSocket更新</Text>
                    </div> */}
                    <div className="feature-item">
                      <InfoCircleOutlined className="feature-icon" />
                      <Text>支持自定义多种翻译服务商（OpenAI、Ollama）</Text>
                    </div>
                  </Space>
                </div>
              </div>
            </Space>
          </Card>

          {/* Error Display */}
          <ErrorDisplay />

          <Divider />

          {/* Provider Configuration */}
          <div className="provider-section">
            <ProviderSelector disabled={isTranslating} />
          </div>

          <Divider />

          {/* Glossary Upload Section (Optional) */}
          <Card title="术语表（可选）" className="upload-card" bordered={false} style={{ marginBottom: 16 }}>
            <GlossaryUpload
              maxSize={1 * 1024 * 1024} // 1MB
              optional={true}
              onGlossaryReady={(glossary) => {
                console.log('Glossary ready with', Object.keys(glossary).length, 'terms');
              }}
            />
          </Card>

          <Divider />

          {/* File Upload Section */}
          <Card title="上传文档" className="upload-card" bordered={false}>
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <FileUpload
                ref={fileUploadRef}
                accept=".md,.markdown"
                placeholder="点击或拖拽Markdown文件到此区域上传"
                maxSize={10 * 1024 * 1024} // 10MB
                label="选择要翻译的Markdown文件"
                onContentReady={handleFileContentReady}
              />

              {/* File Preview */}
              {uploadedFile && fileContent && (
                <div className="file-preview">
                  <Title level={5}>文件预览</Title>
                  <div className="preview-info">
                    <Space direction="vertical" size="small" style={{ width: '100%' }}>
                      <div className="preview-stats">
                        <Space split={<Divider type="vertical" />}>
                          <Text>文件名：{uploadedFile.name}</Text>
                          <Text>大小：{(uploadedFile.size / 1024).toFixed(2)} KB</Text>
                          <Text>字符数：{fileContent.length.toLocaleString()}</Text>
                          <Text>预计翻译时间：~{Math.ceil(fileContent.length / 500)} 秒</Text>
                        </Space>
                      </div>

                      <Alert
                        message="文件已就绪"
                        description="可以开始翻译。翻译过程中会保持原始格式不变。"
                        type="success"
                        showIcon
                      />
                    </Space>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="action-buttons">
                <Space size="middle">
                  <Button
                    type="primary"
                    size="large"
                    icon={<RocketOutlined />}
                    onClick={handleStartTranslation}
                    loading={isTranslating}
                    disabled={!canStartTranslation}
                  >
                    开始翻译
                  </Button>

                  <Button
                    size="large"
                    onClick={handleReset}
                    disabled={isTranslating || !uploadedFile}
                  >
                    重新选择文件
                  </Button>
                </Space>
              </div>
            </Space>
          </Card>
        </div>
      </Content>
    </Layout>
  );
};

export default DocumentUploadPage;