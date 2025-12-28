/**
 * TranslationProgress Page
 *
 * Shows real-time translation progress
 */

import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Layout,
  Typography,
  Button,
  Space,
  Card,
  Statistic,
  Row,
  Col,
  message
} from 'antd';
import {
  TranslationOutlined,
  ArrowLeftOutlined,
  DownloadOutlined,
  EyeOutlined,
  LoadingOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { ProgressDisplay, ErrorDisplay } from '../../components';
import { useTranslationJob, useFileUpload, useTranslationStore } from '../../stores/translationStore';
import './style.css';

const { Header, Content } = Layout;
const { Title, Text } = Typography;

const TranslationProgressPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const {
    currentJobId,
    jobStatus,
    isTranslating,
    translationResult,
    downloadResult,
    cancelTranslation,
    fetchJobStatus
  } = useTranslationJob();

  const { uploadedFileName } = useFileUpload();

  // Get job ID from URL parameter if not in store
  const urlJobId = searchParams.get('jobId');
  const effectiveJobId = currentJobId || urlJobId;

  // Restore job ID to store if it was lost
  useEffect(() => {
    if (urlJobId && !currentJobId) {
      console.log('🔄 Restoring job ID from URL:', urlJobId);
      useTranslationStore.getState().currentJobId = urlJobId;
    }
  }, [urlJobId, currentJobId]);

  // Poll job status when page mounts
  useEffect(() => {
    if (!effectiveJobId) {
      console.log('⚠️ No currentJobId, skipping polling');
      return;
    }

    console.log(`📊 Starting to poll job status for ${effectiveJobId}`);

    // Fetch initial status
    fetchJobStatus(effectiveJobId);

    // Set up polling interval (every 2 seconds)
    const pollInterval = setInterval(() => {
      if (effectiveJobId) {
        console.log(`🔄 Polling status for ${effectiveJobId}...`);
        fetchJobStatus(effectiveJobId);
      }
    }, 2000);

    // Cleanup interval when component unmounts or job completes
    return () => {
      console.log(`🛑 Stopping polling for ${effectiveJobId}`);
      clearInterval(pollInterval);
    };
  }, [effectiveJobId, fetchJobStatus]);

  // Debug log when job status changes
  useEffect(() => {
    console.log('📈 Job status updated:', {
      status: jobStatus?.status,
      progress: jobStatus?.progress,
      isTranslating,
      hasResult: !!translationResult
    });
  }, [jobStatus, isTranslating, translationResult]);

  // Handle back button
  const handleBack = () => {
    if (isTranslating) {
      // Show confirmation if translating
      const shouldCancel = window.confirm(
        '翻译正在进行中，确定要返回吗？这将取消当前的翻译任务。'
      );
      if (shouldCancel) {
        cancelTranslation();
        navigate('/');
      }
    } else {
      navigate('/');
    }
  };

  // Handle view result
  const handleViewResult = () => {
    navigate('/result');
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

  // Handle cancel translation
  const handleCancelTranslation = async () => {
    const shouldCancel = window.confirm(
      '确定要取消翻译吗？已翻译的部分将会丢失。'
    );
    if (shouldCancel) {
      try {
        await cancelTranslation();
        message.info('翻译已取消');
        navigate('/');
      } catch (error) {
        console.error('Cancel failed:', error);
        message.error('取消翻译失败，请重试');
      }
    }
  };

  // Get status info
  const getStatusInfo = () => {
    if (!jobStatus) {
      return {
        icon: <LoadingOutlined />,
        color: '#1890ff',
        text: '准备中...'
      };
    }

    switch (jobStatus.status) {
      case 'completed':
        return {
          icon: <CheckCircleOutlined />,
          color: '#52c41a',
          text: '翻译完成'
        };
      case 'error':
        return {
          icon: <ExclamationCircleOutlined />,
          color: '#ff4d4f',
          text: '翻译失败'
        };
      case 'translating':
        return {
          icon: <LoadingOutlined spin />,
          color: '#1890ff',
          text: '翻译中...'
        };
      default:
        return {
          icon: <LoadingOutlined />,
          color: '#8c8c8c',
          text: jobStatus.status
        };
    }
  };

  const statusInfo = getStatusInfo();

  return (
    <Layout className="translation-progress-page">
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
            <TranslationOutlined className="page-icon" />
            <div>
              <Title level={2} className="page-title">
                翻译进度
              </Title>
              <Text className="page-subtitle">
                {uploadedFileName ? `${uploadedFileName} - 实时翻译状态` : '实时翻译状态'}
              </Text>
            </div>
            <div className="status-indicator">
              <Space>
                {statusInfo.icon}
                <Text style={{ color: statusInfo.color, fontWeight: 500 }}>
                  {statusInfo.text}
                </Text>
              </Space>
            </div>
          </Space>
        </div>
      </Header>

      <Content className="page-content">
        <div className="content-wrapper">
          {/* Job Information */}
          {currentJobId && (
            <Card className="job-info-card" bordered={false}>
              <Row gutter={[24, 16]}>
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title="任务ID"
                    value={currentJobId.slice(0, 8)}
                    suffix={`...${currentJobId.slice(-4)}`}
                    prefix={<Text code style={{ fontSize: 16 }}>#</Text>}
                  />
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title="当前进度"
                    value={jobStatus?.progress || 0}
                    suffix="%"
                    prefix={isTranslating ? <LoadingOutlined spin /> : null}
                  />
                </Col>
                {uploadedFileName && (
                  <Col xs={24} sm={12} md={6}>
                    <Statistic
                      title="文件名"
                      value={uploadedFileName}
                      style={{ wordBreak: 'break-all' }}
                    />
                  </Col>
                )}
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title="状态"
                    value={statusInfo.text}
                    prefix={statusInfo.icon}
                    valueStyle={{ color: statusInfo.color }}
                  />
                </Col>
              </Row>
            </Card>
          )}

          {/* Error Display */}
          <ErrorDisplay />

          {/* Progress Display */}
          <ProgressDisplay
            progress={jobStatus?.progress || 0}
            status={jobStatus?.status || 'idle'}
            currentPhase={jobStatus?.status === 'translating' ? 'llm_request' : jobStatus?.status === 'completed' ? 'completed' : 'validating'}
            estimatedTimeRemaining={jobStatus?.estimated_completion ? new Date(jobStatus.estimated_completion).getTime() : null}
            warnings={jobStatus?.warnings || []}
            canCancel={isTranslating}
            onCancel={handleCancelTranslation}
          />

          {/* Action Buttons */}
          <Card className="action-card" bordered={false}>
            <div className="action-buttons">
              <Space size="middle" wrap>
                {jobStatus?.status === 'completed' && translationResult && (
                  <>
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
                      onClick={handleViewResult}
                    >
                      查看翻译结果
                    </Button>
                  </>
                )}

                {isTranslating && (
                  <Button
                    danger
                    size="large"
                    onClick={handleCancelTranslation}
                  >
                    取消翻译
                  </Button>
                )}

                <Button
                  size="large"
                  icon={<ArrowLeftOutlined />}
                  onClick={handleBack}
                >
                  返回首页
                </Button>
              </Space>
            </div>
          </Card>

          {/* Tips */}
          <Card className="tips-card" bordered={false}>
            <Title level={4}>使用提示</Title>
            <div className="tips-content">
              <Space direction="vertical" size="small">
                <div className="tip-item">
                  <Text>• 翻译过程中请不要关闭此页面，否则翻译进度将无法跟踪</Text>
                </div>
                <div className="tip-item">
                  <Text>• 翻译完成后可以立即下载结果，结果将保留原始Markdown格式</Text>
                </div>
                <div className="tip-item">
                  <Text>• 如果翻译失败，请检查文件内容或更换翻译服务商后重试</Text>
                </div>
                <div className="tip-item">
                  <Text>• 支持的文件格式：.md, .markdown，文件大小不超过10MB</Text>
                </div>
              </Space>
            </div>
          </Card>
        </div>
      </Content>
    </Layout>
  );
};

export default TranslationProgressPage;