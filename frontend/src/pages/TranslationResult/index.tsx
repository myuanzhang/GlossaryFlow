/**
 * TranslationResult Page
 *
 * Shows translation results with download and preview functionality
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Layout,
  Typography,
  Button,
  Space,
  Card,
  Alert,
  Row,
  Col,
  Divider,
  message,
  Spin,
  Empty,
  Tooltip,
  Modal
} from 'antd';
import {
  FileTextOutlined,
  ArrowLeftOutlined,
  DownloadOutlined,
  CopyOutlined,
  EyeOutlined,
  CheckCircleOutlined,
  InfoCircleOutlined,
  ReloadOutlined,
  ShareAltOutlined,
  FullscreenOutlined
} from '@ant-design/icons';
import { ErrorDisplay } from '../../components';
import { useTranslationJob, useFileUpload } from '../../stores/translationStore';
import type { TranslationOutput } from '../../types/api';
import './style.css';

const { Header, Content } = Layout;
const { Title, Text, Paragraph } = Typography;

const TranslationResultPage: React.FC = () => {
  const navigate = useNavigate();
  const {
    currentJobId,
    translationResult,
    downloadResult,
    isTranslating
  } = useTranslationJob();

  const { uploadedFileName } = useFileUpload();
  const [previewContent, setPreviewContent] = useState<string>('');
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [copied, setCopied] = useState(false);

  // Load preview content when result is available
  useEffect(() => {
    if (translationResult && !previewContent) {
      loadPreviewContent();
    }
  }, [translationResult]);

  // Load preview content
  const loadPreviewContent = async () => {
    if (!currentJobId) return;

    setIsPreviewLoading(true);
    try {
      const content = await fetchTranslationResult();
      setPreviewContent(content);
    } catch (error) {
      console.error('Failed to load preview:', error);
      message.error('加载预览内容失败');
    } finally {
      setIsPreviewLoading(false);
    }
  };

  // Fetch translation result
  const fetchTranslationResult = async (): Promise<string> => {
    if (!currentJobId) {
      throw new Error('No job ID available');
    }

    const response = await fetch(`http://localhost:8000/api/v1/translate/${currentJobId}/result`, {
      method: 'GET',
      headers: {
        'Content-Type': 'text/plain',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.text();
  };

  // Handle back button
  const handleBack = () => {
    navigate('/progress');
  };

  // Handle download
  const handleDownload = async () => {
    try {
      await downloadResult();
      message.success('文件下载成功！');
    } catch (error) {
      console.error('Download failed:', error);
      message.error('文件下载失败，请重试');
    }
  };

  // Handle copy to clipboard
  const handleCopyToClipboard = async () => {
    try {
      if (!previewContent) {
        await loadPreviewContent();
      }
      await navigator.clipboard.writeText(previewContent);
      setCopied(true);
      message.success('已复制到剪贴板');
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Copy failed:', error);
      message.error('复制失败，请重试');
    }
  };

  // Handle start new translation
  const handleNewTranslation = () => {
    // Reset state and navigate to home
    navigate('/');
  };

  // Handle show preview
  const handleShowPreview = async () => {
    if (!previewContent) {
      await loadPreviewContent();
    }
    setShowPreviewModal(true);
  };

  // Format file size
  const formatFileSize = (content: string): string => {
    const bytes = new Blob([content]).size;
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Render markdown preview
  const renderMarkdownPreview = (content: string) => {
    return (
      <div className="markdown-preview">
        <pre className="markdown-content">{content}</pre>
      </div>
    );
  };

  // Show loading state if still translating
  if (isTranslating) {
    return (
      <Layout className="translation-result-page">
        <Content className="page-content">
          <div className="loading-container">
            <Spin size="large" />
            <Title level={3}>翻译进行中...</Title>
            <Text>请稍候，正在为您生成翻译结果</Text>
          </div>
        </Content>
      </Layout>
    );
  }

  // Show empty state if no result
  if (!translationResult) {
    return (
      <Layout className="translation-result-page">
        <Header className="page-header">
          <div className="header-content">
            <Space size="large">
              <Button
                type="text"
                icon={<ArrowLeftOutlined />}
                onClick={handleBack}
                className="back-button"
              >
                返回
              </Button>
              <FileTextOutlined className="page-icon" />
              <Title level={2} className="page-title">
                翻译结果
              </Title>
            </Space>
          </div>
        </Header>

        <Content className="page-content">
          <div className="content-wrapper">
            <Empty
              description="暂无翻译结果"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            >
              <Button type="primary" onClick={handleBack}>
                返回进度页面
              </Button>
            </Empty>
          </div>
        </Content>
      </Layout>
    );
  }

  return (
    <Layout className="translation-result-page">
      <Header className="page-header">
        <div className="header-content">
          <Space size="large">
            <Button
              type="text"
              icon={<ArrowLeftOutlined />}
              onClick={handleBack}
              className="back-button"
            >
              返回
            </Button>
            <CheckCircleOutlined className="page-icon success" />
            <div>
              <Title level={2} className="page-title">
                翻译完成
              </Title>
              <Text className="page-subtitle">
                {uploadedFileName ? `${uploadedFileName} - 翻译结果` : '翻译结果'}
              </Text>
            </div>
          </Space>
        </div>
      </Header>

      <Content className="page-content">
        <div className="content-wrapper">
          {/* Result Metadata */}
          <Card className="metadata-card" bordered={false}>
            <Title level={4}>翻译信息</Title>
            <Row gutter={[24, 16]}>
              <Col xs={24} sm={12} md={8}>
                <div className="metadata-item">
                  <Text type="secondary">翻译服务商</Text>
                  <div className="metadata-value">
                    <Text strong>{translationResult.metadata.provider_used}</Text>
                  </div>
                </div>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <div className="metadata-item">
                  <Text type="secondary">使用模型</Text>
                  <div className="metadata-value">
                    <Text strong>{translationResult.metadata.model_used}</Text>
                  </div>
                </div>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <div className="metadata-item">
                  <Text type="secondary">术语表应用</Text>
                  <div className="metadata-value">
                    <Text strong>
                      {translationResult.metadata.glossary_applied ? '是' : '否'}
                    </Text>
                  </div>
                </div>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <div className="metadata-item">
                  <Text type="secondary">预估文件大小</Text>
                  <div className="metadata-value">
                    <Text strong>
                      {formatFileSize(translationResult.translated_markdown)}
                    </Text>
                  </div>
                </div>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <div className="metadata-item">
                  <Text type="secondary">字符数</Text>
                  <div className="metadata-value">
                    <Text strong>
                      {translationResult.translated_markdown.length.toLocaleString()}
                    </Text>
                  </div>
                </div>
              </Col>
              <Col xs={24} sm={12} md={8}>
                <div className="metadata-item">
                  <Text type="secondary">任务ID</Text>
                  <div className="metadata-value">
                    <Text code copyable={{ text: currentJobId || '' }}>
                      {currentJobId?.slice(0, 8)}...{currentJobId?.slice(-4)}
                    </Text>
                  </div>
                </div>
              </Col>
            </Row>

            {/* Warnings */}
            {translationResult.metadata.warnings.length > 0 && (
              <div style={{ marginTop: 24, paddingTop: 24, borderTop: '1px solid #f0f0f0' }}>
                <Title level={5}>
                  <InfoCircleOutlined style={{ color: '#faad14', marginRight: 8 }} />
                  注意事项
                </Title>
                {translationResult.metadata.warnings.map((warning, index) => (
                  <Alert
                    key={index}
                    message={warning}
                    type="warning"
                    showIcon
                    size="small"
                    style={{ marginBottom: 8 }}
                  />
                ))}
              </div>
            )}
          </Card>

          {/* Error Display */}
          <ErrorDisplay />

          {/* Action Buttons */}
          <Card className="action-card" bordered={false}>
            <div className="action-buttons">
              <Space size="middle" wrap>
                <Button
                  type="primary"
                  size="large"
                  icon={<DownloadOutlined />}
                  onClick={handleDownload}
                >
                  下载翻译结果
                </Button>

                <Button
                  size="large"
                  icon={<EyeOutlined />}
                  onClick={handleShowPreview}
                  loading={isPreviewLoading}
                >
                  预览内容
                </Button>

                <Button
                  size="large"
                  icon={<CopyOutlined />}
                  onClick={handleCopyToClipboard}
                  disabled={!previewContent}
                >
                  {copied ? '已复制' : '复制到剪贴板'}
                </Button>

                <Button
                  size="large"
                  icon={<ReloadOutlined />}
                  onClick={handleNewTranslation}
                >
                  开始新翻译
                </Button>
              </Space>
            </div>
          </Card>

          {/* Quick Preview */}
          {previewContent && (
            <Card
              title="内容预览（前500字符）"
              className="preview-card"
              bordered={false}
              extra={
                <Button
                  type="link"
                  icon={<FullscreenOutlined />}
                  onClick={handleShowPreview}
                >
                  全屏预览
                </Button>
              }
            >
              <div className="quick-preview">
                <pre className="preview-content">
                  {previewContent.slice(0, 500)}
                  {previewContent.length > 500 && '...'}
                </pre>
              </div>
            </Card>
          )}

          {/* Tips */}
          <Card className="tips-card" bordered={false}>
            <Title level={4}>使用提示</Title>
            <div className="tips-content">
              <Space direction="vertical" size="small">
                <div className="tip-item">
                  <Text>• 翻译结果保留了原始Markdown格式，可以直接在任何支持Markdown的编辑器中使用</Text>
                </div>
                <div className="tip-item">
                  <Text>• 建议下载后仔细检查翻译结果，特别是专业术语和上下文相关的表达</Text>
                </div>
                <div className="tip-item">
                  <Text>• 如需重新翻译，可以返回首页重新上传文件</Text>
                </div>
                <div className="tip-item">
                  <Text>• 翻译结果会保留在服务器24小时，请及时下载保存</Text>
                </div>
              </Space>
            </div>
          </Card>
        </div>
      </Content>

      {/* Full Preview Modal */}
      <Modal
        title="翻译结果预览"
        open={showPreviewModal}
        onCancel={() => setShowPreviewModal(false)}
        footer={[
          <Button key="copy" icon={<CopyOutlined />} onClick={handleCopyToClipboard}>
            复制内容
          </Button>,
          <Button key="download" type="primary" icon={<DownloadOutlined />} onClick={handleDownload}>
            下载文件
          </Button>,
        ]}
        width="90%"
        style={{ top: 20 }}
        className="preview-modal"
      >
        <div className="modal-preview-content">
          {isPreviewLoading ? (
            <div className="preview-loading">
              <Spin size="large" />
              <Text>加载预览内容中...</Text>
            </div>
          ) : (
            renderMarkdownPreview(previewContent)
          )}
        </div>
      </Modal>
    </Layout>
  );
};

export default TranslationResultPage;