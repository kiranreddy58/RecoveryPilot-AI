import { useEffect, useState, useRef, useCallback } from 'react';
import { API_V1 } from '../api/client';

export interface StreamEvent {
  event: string;
  timestamp: string;
  data: any;
}

/**
 * SSE streaming hook for real-time recovery events.
 *
 * On Vercel serverless deployments, SSE is not supported.
 * The hook detects this by checking the first response from the stream
 * endpoint — if it returns JSON with SERVERLESS_MODE, it stops retrying.
 */
export function useRecoveryStream(onEvent?: (event: StreamEvent) => void) {
  const [connected, setConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<StreamEvent | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const callbackRef = useRef(onEvent);
  const serverlessModeRef = useRef(false);

  useEffect(() => {
    callbackRef.current = onEvent;
  }, [onEvent]);

  const connect = useCallback(() => {
    // Don't reconnect if we detected serverless mode
    if (serverlessModeRef.current) return;

    try {
      const url = `${API_V1}/stream/events`;
      const es = new EventSource(url);

      es.onopen = () => {
        setConnected(true);
      };

      es.onmessage = (e) => {
        try {
          if (!e.data || e.data.startsWith(':')) return;
          const parsed: StreamEvent = JSON.parse(e.data);

          // Detect serverless mode response and stop reconnecting
          if (parsed.event === 'SERVERLESS_MODE') {
            serverlessModeRef.current = true;
            setConnected(false);
            es.close();
            return;
          }

          setLastEvent(parsed);
          if (callbackRef.current) {
            callbackRef.current(parsed);
          }
        } catch (err) {
          // Ignore heartbeat or non-json frame
        }
      };

      es.onerror = () => {
        setConnected(false);
        es.close();
        // Don't reconnect if in serverless mode
        if (!serverlessModeRef.current) {
          // Reconnect after 5 seconds (with backoff to avoid log flooding)
          setTimeout(connect, 5000);
        }
      };

      eventSourceRef.current = es;
    } catch (e) {
      setConnected(false);
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [connect]);

  return { connected, lastEvent };
}
