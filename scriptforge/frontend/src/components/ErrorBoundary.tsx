import { Component, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="flex items-center justify-center h-64">
            <div className="text-center space-y-3">
              <p className="text-lg font-semibold text-text-primary">页面出了点问题</p>
              <p className="text-sm text-text-secondary">请刷新页面重试</p>
              <button
                onClick={() => this.setState({ hasError: false })}
                className="px-4 py-2 bg-brand text-white rounded-md text-sm hover:bg-brand-hover transition-colors"
              >
                重试
              </button>
            </div>
          </div>
        )
      );
    }
    return this.props.children;
  }
}
