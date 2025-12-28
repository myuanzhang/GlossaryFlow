/**
 * ProgressDisplay Component
 *
 * Shows translation progress with real-time updates
 */

import React from 'react';
import { Progress, Button, Alert, Typography, Space } from 'antd';
import {
  CloseOutlined,
  LoadingOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import { useTranslationJob } from '../../stores/translationStore';
import type { ProgressDisplayProps } from '../../types/ui';
import './style.css';
import './enhanced.css';

const { Text, Title } = Typography;

// Phase mapping for better user experience
const phaseLabels: Record<string, string> = {
  'validating': '验证文档',
  'prompt_building': '构建翻译提示',
  'llm_request': 'AI翻译中',
  'output_cleaning': '整理输出',
  'completed': '翻译完成'
};

const phaseIcons: Record<string, React.ReactNode> = {
  'validating': <LoadingOutlined spin />,
  'prompt_building': <LoadingOutlined spin />,
  'llm_request': <LoadingOutlined spin />,
  'output_cleaning': <LoadingOutlined spin />,
  'completed': <CheckCircleOutlined style={{ color: '#52c41a' }} />
};

const ProgressDisplay: React.FC<ProgressDisplayProps> = ({
  canCancel = true,
  onCancel
}) => {
  const {
    jobStatus,
    isTranslating,
    translationResult,
    cancelTranslation
  } = useTranslationJob();

  const handleCancel = async () => {
    if (onCancel) {
      onCancel();
    } else {
      await cancelTranslation();
    }
  };

  if (!jobStatus && !isTranslating) {
    return null;
  }

  const { progress, status, warnings } = jobStatus || {
    progress: 0,
    status: 'idle',
    warnings: []
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'completed':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'error':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'translating':
      case 'validating':
        return <LoadingOutlined spin />;
      default:
        return <ClockCircleOutlined style={{ color: '#8c8c8c' }} />;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'completed':
        return '#52c41a';
      case 'error':
        return '#ff4d4f';
      case 'translating':
      case 'validating':
        return '#1890ff';
      default:
        return '#8c8c8c';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'idle':
        return '准备中';
      case 'validating':
        return '验证文档';
      case 'translating':
        return '翻译中';
      case 'completed':
        return '翻译完成';
      case 'error':
        return '翻译失败';
      default:
        return status;
    }
  };

  // Get current phase from warnings or status
  const getCurrentPhase = () => {
    // Try to extract phase from warnings
    for (const warning of warnings) {
      const phase = Object.keys(phaseLabels).find(key =>
        warning.toLowerCase().includes(key) || warning.toLowerCase().includes(phaseLabels[key])
      );
      if (phase) {
        return phase;
      }
    }

    // Fallback to status
    if (status === 'translating') return 'llm_request';
    if (status === 'validating') return 'validating';
    if (status === 'completed') return 'completed';

    return 'validating';
  };

  const currentPhase = getCurrentPhase();

  return (
    <div className="progress-display">
      <div className="progress-header">
        <div className="progress-title">
          <Title level={4} style={{ margin: 0 }}>
            翻译进度
          </Title>
          <Space>
            {getStatusIcon()}
            <Text strong style={{ color: getStatusColor() }}>
              {getStatusText()}
            </Text>
          </Space>
        </div>

        {canCancel && isTranslating && (
          <Button
            type="text"
            icon={<CloseOutlined />}
            onClick={handleCancel}
            size="small"
            danger
          >
            取消翻译
          </Button>
        )}
      </div>

      <div className="progress-content">
        <Progress
          percent={progress}
          status={status === 'error' ? 'exception' : status === 'completed' ? 'success' : 'active'}
          strokeColor={{
            '0%': '#108ee9',
            '100%': '#87d068',
          }}
          strokeWidth={8}
          className="progress-bar"
        />

        <div className="progress-details">
          <div className="phase-info">
            <Space>
              {status !== 'completed' ? phaseIcons[currentPhase] : <CheckCircleOutlined style={{ color: '#52c41a' }} />}
              <Text>当前阶段：{phaseLabels[currentPhase]}</Text>
            </Space>
          </div>

          <div className="progress-percentage">
            <Text type="secondary">{progress}% 完成</Text>
          </div>
        </div>

        {/* Show warnings */}
        {warnings.length > 0 && (
          <div className="progress-warnings">
            {warnings.map((warning, index) => (
              <Alert
                key={index}
                message={warning}
                type="warning"
                showIcon
                style={{ marginBottom: 8 }}
              />
            ))}
          </div>
        )}

        {/* Show completion info */}
        {status === 'completed' && translationResult && (
          <div className="completion-info">
            <Alert
              message="翻译完成！"
              description={
                <div>
                  <p>翻译服务商：{translationResult.metadata.provider_used}</p>
                  <p>使用模型：{translationResult.metadata.model_used}</p>
                  {translationResult.metadata.glossary_applied && (
                    <p>已应用术语表</p>
                  )}
                </div>
              }
              type="success"
              showIcon
            />
          </div>
        )}

        {/* Show error info */}
        {status === 'error' && (
          <div className="error-info">
            <Alert
              message="翻译失败"
              description="请检查所选模型的API配置是否正确，修改后，请重启后端服务"
              type="error"
              showIcon
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default ProgressDisplay;