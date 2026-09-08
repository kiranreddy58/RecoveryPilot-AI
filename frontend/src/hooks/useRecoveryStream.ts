import { useEffect, useState, useRef } from 'react';
import { API_V1 } from '../api/client';

export interface StreamEvent {
  event: string;
  timestamp: string;
  data: any;
}

/**
 * SSE streaming hook for real-time recovery events.
 *
 * In serverless environments (e.g. Vercel), long-lived SSE connections are not
 * supported. The hook automatically falls back to lightweight polling so the UI
 * updates reliably without spamming EventSource connection errors.
 */
export function useRecoveryStream(onEvent?: (event: StreamEvent) => void) {
  const [connected, setConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<StreamEvent | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const callbackRef = useRef(onEvent);
  const isServerless = typeof window !== 'undefined' && window.location.hostname.includes('vercel.app');

  useEffect(() => {
    callbackRef.current = onEvent;
  }, [onEvent]);

  useEffect(() => {
    // If deployed on Vercel serverless, use interval polling instead of SSE to prevent MIME/timeout errors
    if (isServerless) {
      const pollTimer = setInterval(() => {
        if (callbackRef.current) {
          callbackRef.current({
            event: 'POLL_TICK',
            timestamp: new Date().toISOString(),
            data: {},
          });
        }
      }, 10000);

      return () => clearInterval(pollTimer);
    }

    // On local/persistent server: connect to full SSE stream
    let retryCount = 0;
    let timer: ReturnType<typeof setTimeout> | null = null;
    let es: EventSource | null = null;

    const connect = () => {
      try {
        const url = `${API_V1}/stream/events`;
        es = new EventSource(url);

        es.onopen = () => {
          setConnected(true);
          retryCount = 0;
        };

        es.onmessage = (e) => {
          try {
            if (!e.data || e.data.startsWith(':')) return;
            const parsed: StreamEvent = JSON.parse(e.data);

            if (parsed.event === 'SERVERLESS_MODE') {
              setConnected(false);
              es?.close();
              return;
            }

            setLastEvent(parsed);
            if (callbackRef.current) {
              callbackRef.current(parsed);
            }
          } catch {
            // Ignore heartbeat or malformed frames
          }
        };

        es.onerror = () => {
          setConnected(false);
          es?.close();
          retryCount++;
          // Only retry up to 2 times to avoid spamming the console if server is down
          if (retryCount <= 2) {
            timer = setTimeout(connect, 10000);
          }
        };

        eventSourceRef.current = es;
      } catch {
        setConnected(false);
      }
    };

    connect();

    return () => {
      if (timer) clearTimeout(timer);
      if (es) es.close();
      if (eventSourceRef.current) eventSourceRef.current.close();
    };
  }, [isServerless]);

  return { connected, lastEvent };
}

