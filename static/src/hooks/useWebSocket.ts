import { useEffect, useRef, useState } from 'react';

interface WebSocketMessage {
  type: 'progress' | 'complete' | 'error';
  task_id: string;
  progress?: number;
  message?: string;
  status?: string;
  result?: any;
  error?: string;
  timestamp: number;
}

interface UseWebSocketReturn {
  progress: number;
  status: string;
  result: any;
  error: string | null;
  connected: boolean;
  sendMessage: (message: any) => void;
  disconnect: () => void;
  reset: () => void;
}

function buildWebSocketUrl(taskId: string): string {
  const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

  if (!apiBaseUrl && typeof window !== 'undefined') {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const isViteDevServer = window.location.port === '3000' || window.location.port === '5173';
    const host = isViteDevServer ? `${window.location.hostname}:8001` : window.location.host;
    return `${protocol}//${host}/ws/solve/${taskId}`;
  }

  return apiBaseUrl
    .replace('http://', 'ws://')
    .replace('https://', 'wss://') + `/ws/solve/${taskId}`;
}

export function useWebSocket(taskId: string): UseWebSocketReturn {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('idle');
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pendingMessageRef = useRef<any | null>(null);
  const shouldReconnectRef = useRef(true);

  const reset = () => {
    setProgress(0);
    setStatus('idle');
    setResult(null);
    setError(null);
    pendingMessageRef.current = null;
  };

  const connect = () => {
    if (!taskId) {
      return;
    }

    shouldReconnectRef.current = true;
    const ws = new WebSocket(buildWebSocketUrl(taskId));

    ws.onopen = () => {
      setConnected(true);
      setError(null);
      if (pendingMessageRef.current) {
        ws.send(JSON.stringify(pendingMessageRef.current));
        pendingMessageRef.current = null;
      }
    };

    ws.onmessage = (event) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data);

        switch (data.type) {
          case 'progress':
            setProgress(data.progress || 0);
            setStatus(data.status || 'running');
            break;
          case 'complete':
            setProgress(1);
            setStatus('complete');
            setResult(data.result);
            break;
          case 'error':
            setStatus('error');
            setError(data.error || 'Unknown WebSocket error');
            break;
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    ws.onerror = () => {
      setError('WebSocket connection error');
      setConnected(false);
    };

    ws.onclose = () => {
      setConnected(false);

      if (shouldReconnectRef.current && status !== 'complete' && status !== 'error') {
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 3000);
      }
    };

    wsRef.current = ws;
  };

  useEffect(() => {
    connect();

    return () => {
      shouldReconnectRef.current = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [taskId]);

  const sendMessage = (message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      return;
    }

    pendingMessageRef.current = message;
  };

  const disconnect = () => {
    shouldReconnectRef.current = false;
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
  };

  return {
    progress,
    status,
    result,
    error,
    connected,
    sendMessage,
    disconnect,
    reset,
  };
}
