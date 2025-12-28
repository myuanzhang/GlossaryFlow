/**
 * Main Application Component
 *
 * Router configuration and global styles
 */

import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, App as AntApp } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { ErrorDisplay } from './components';
import {
  DocumentUploadPage,
  TranslationProgressPage,
  TranslationResultPage
} from './pages';
import { useSystemStatus, useTranslationJob } from './stores/translationStore';
import 'antd/dist/reset.css';
import './App.css';
import './styles/enhanced.css';

const App: React.FC = () => {
  const { checkSystemHealth } = useSystemStatus();
  const { resetState } = useTranslationJob();

  // Initialize application
  useEffect(() => {
    // Check system health on app start
    checkSystemHealth();

    // Reset state on page refresh
    const handleBeforeUnload = () => {
      resetState();
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, []);

  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#667eea',
          colorSuccess: '#52c41a',
          colorWarning: '#faad14',
          colorError: '#ff4d4f',
          colorInfo: '#1890ff',
          borderRadius: 12,
          fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
          fontSize: 14,
          fontWeightStrong: 600,
        },
        components: {
          Layout: {
            bodyBg: '#f5f7fa',
            headerBg: '#ffffff',
          },
          Card: {
            borderRadius: 16,
          },
          Button: {
            borderRadius: 10,
            controlHeight: 48,
            fontWeight: 600,
          },
          Input: {
            borderRadius: 10,
            controlHeight: 48,
          },
          Select: {
            borderRadius: 10,
            controlHeight: 48,
          },
          Upload: {
            borderRadius: 12,
          },
          Progress: {
            borderRadius: 10,
          },
          Alert: {
            borderRadius: 12,
          },
          Tag: {
            borderRadius: 8,
          },
          Divider: {
            marginVertical: 24,
          },
        },
      }}
    >
      <AntApp>
        <Router>
          <div className="app">
            <Routes>
              {/* Default route - Document Upload */}
              <Route path="/" element={<DocumentUploadPage />} />

              {/* Translation Progress */}
              <Route path="/progress" element={<TranslationProgressPage />} />

              {/* Translation Result */}
              <Route path="/result" element={<TranslationResultPage />} />

              {/* Catch all - redirect to home */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>

            {/* Global Error Display */}
            <div className="global-error-display">
              <ErrorDisplay />
            </div>
          </div>
        </Router>
      </AntApp>
    </ConfigProvider>
  );
};

export default App;
