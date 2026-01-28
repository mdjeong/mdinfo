'use client';

import { Component, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="error-boundary">
          <h2>문제가 발생했습니다</h2>
          <p>페이지를 표시하는 중 오류가 발생했습니다.</p>
          {this.state.error && (
            <details>
              <summary>오류 상세</summary>
              <pre>{this.state.error.message}</pre>
            </details>
          )}
          <button onClick={this.handleReset} className="retry-button">
            다시 시도
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
