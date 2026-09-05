import { useEffect, useState, useRef, useCallback } from 'react';
import { API_V1 } from '../api/client';

export interface StreamEvent {
  event: string;
  timestamp: string;
  data: any;
}

export function useRecoveryStream(onEvent?: (event: StreamEvent) => void) {
  const [connected, setConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<StreamEvent | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const callbackRef = useRef(onEvent);

  useEffect(() => {
    callbackRef.current = onEvent;
  }, [onEvent]);

  const connect = useCallback(() => {
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
        // Reconnect after 3 seconds
        setTimeout(connect, 3000);
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
