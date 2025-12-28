/**
 * ErrorDisplay Component
 *
 * Shows error messages with retry and dismiss actions
 */

import React from 'react';
import { Alert, Button, Space, Typography, Collapse } from 'antd';
import {
  ExclamationCircleOutlined,
  ReloadOutlined,
  CloseOutlined,
  BugOutlined
} from '@ant-design/icons';
import { useNotifications } from '../../stores/translationStore';
import type { ErrorDisplayProps } from '../../types/ui';

const { Text, Paragraph } = Typography;
const { Panel } = Collapse;

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  onRetry,
  onDismiss,
  showRetry = true
}) => {
  const { errors, warnings, clearErrors, clearWarnings } = useNotifications();

  const handleRetry = () => {
    clearErrors();
    if (onRetry) {
      onRetry();
    }
  };

  const handleDismiss = () => {
    clearErrors();
    if (onDismiss) {
      onDismiss();
    }
  };

  const handleErrorDetails = (error: string, index: number) => {
    // Try to extract structured error information
    try {
      const errorObj = JSON.parse(error);
      return {
        title: errorObj.error?.message || error,
        details: errorObj.error?.details,
        code: errorObj.error?.code
      };
    } catch {
      return {
        title: error,
        details: null,
        code: null
      };
    }
  };

  if (errors.length === 0 && warnings.length === 0) {
    return null;
  }

  return (
    <div className="error-display">
      {/* Error Messages */}
      {errors.length > 0 && (
        <div className="error-section">
          <Alert
            message={
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <Space>
                  <ExclamationCircleOutlined />
                  <Text strong>
                    {errors.length === 1 ? '发生错误' : `发生 ${errors.length} 个错误`}
                  </Text>
                </Space>

                {errors.map((error, index) => {
                  const errorInfo = handleErrorDetails(error, index);
                  return (
                    <div key={index} className="error-item">
                      <Text>{errorInfo.title}</Text>
                      {errorInfo.details && (
                        <Collapse ghost size="small" className="error-details">
                          <Panel
                            header={
                              <Space>
                                <BugOutlined />
                                <Text type="secondary">查看详细信息</Text>
                              </Space>
                            }
                            key="details"
                          >
                            <div className="error-details-content">
                              {errorInfo.code && (
                                <div className="error-code">
                                  <Text strong>错误代码：</Text>
                                  <Text code>{errorInfo.code}</Text>
                                </div>
                              )}
                              <div className="error-detail-text">
                                <Text strong>详细信息：</Text>
                                <pre>{JSON.stringify(errorInfo.details, null, 2)}</pre>
                              </div>
                            </div>
                          </Panel>
                        </Collapse>
                      )}
                    </div>
                  );
                })}
              </Space>
            }
            type="error"
            showIcon={false}
            action={
              <Space>
                {showRetry && onRetry && (
                  <Button
                    type="primary"
                    size="small"
                    icon={<ReloadOutlined />}
                    onClick={handleRetry}
                  >
                    重试
                  </Button>
                )}
                <Button
                  type="text"
                  size="small"
                  icon={<CloseOutlined />}
                  onClick={handleDismiss}
                >
                  关闭
                </Button>
              </Space>
            }
            className="error-alert"
            closable={false}
          />
        </div>
      )}

      {/* Warning Messages */}
      {warnings.length > 0 && (
        <div className="warning-section">
          <Alert
            message={
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <Space>
                  <ExclamationCircleOutlined style={{ color: '#faad14' }} />
                  <Text strong style={{ color: '#faad14' }}>
                    {warnings.length === 1 ? '注意事项' : ` ${warnings.length} 个注意事项`}
                  </Text>
                </Space>

                {warnings.map((warning, index) => (
                  <div key={index} className="warning-item">
                    <Text>{warning}</Text>
                  </div>
                ))}
              </Space>
            }
            type="warning"
            showIcon={false}
            action={
              <Button
                type="text"
                size="small"
                icon={<CloseOutlined />}
                onClick={clearWarnings}
              >
                关闭
              </Button>
            }
            className="warning-alert"
            closable={false}
          />
        </div>
      )}
    </div>
  );
};

// Single error display component for specific errors
interface SingleErrorDisplayProps {
  error: string;
  title?: string;
  onRetry?: () => void;
  onDismiss?: () => void;
  showRetry?: boolean;
  showDetails?: boolean;
}

export const SingleErrorDisplay: React.FC<SingleErrorDisplayProps> = ({
  error,
  title = '错误',
  onRetry,
  onDismiss,
  showRetry = true,
  showDetails = true
}) => {
  const handleErrorDetails = (error: string) => {
    try {
      const errorObj = JSON.parse(error);
      return {
        details: errorObj.error?.details,
        code: errorObj.error?.code
      };
    } catch {
      return {
        details: null,
        code: null
      };
    }
  };

  const errorInfo = handleErrorDetails(error);

  return (
    <Alert
      message={
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          <Space>
            <ExclamationCircleOutlined />
            <Text strong>{title}</Text>
          </Space>
          <Text>{error}</Text>

          {showDetails && errorInfo.details && (
            <Collapse ghost size="small" className="error-details">
              <Panel
                header={
                  <Space>
                    <BugOutlined />
                    <Text type="secondary">查看详细信息</Text>
                  </Space>
                }
                key="details"
              >
                <div className="error-details-content">
                  {errorInfo.code && (
                    <div className="error-code">
                      <Text strong>错误代码：</Text>
                      <Text code>{errorInfo.code}</Text>
                    </div>
                  )}
                  <div className="error-detail-text">
                    <Text strong>详细信息：</Text>
                    <pre>{JSON.stringify(errorInfo.details, null, 2)}</pre>
                  </div>
                </div>
              </Panel>
            </Collapse>
          )}
        </Space>
      }
      type="error"
      action={
        <Space>
          {showRetry && onRetry && (
            <Button
              type="primary"
              size="small"
              icon={<ReloadOutlined />}
              onClick={onRetry}
            >
              重试
            </Button>
          )}
          {onDismiss && (
            <Button
              type="text"
              size="small"
              icon={<CloseOutlined />}
              onClick={onDismiss}
            >
              关闭
            </Button>
          )}
        </Space>
      }
      className="error-alert"
    />
  );
};

export default ErrorDisplay;