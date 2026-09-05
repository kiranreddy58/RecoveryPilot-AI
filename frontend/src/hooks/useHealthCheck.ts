import { useState, useEffect, useCallback } from 'react';
import { apiClient, HealthResponse } from '../api/client';
import { BackendStatus } from '../types';

interface UseHealthCheckResult {
  status: BackendStatus;
  healthData: HealthResponse | null;
  lastChecked: Date | null;
  checkNow: () => void;
}

export function useHealthCheck(intervalMs: number = 30000): UseHealthCheckResult {
  const [status, setStatus] = useState<BackendStatus>('CONNECTING');
  const [healthData, setHealthData] = useState<HealthResponse | null>(null);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const checkHealth = useCallback(async () => {
    try {
      const data = await apiClient.getHealth();
      setHealthData(data);
      setStatus('ONLINE');
    } catch {
      setHealthData(null);
      setStatus('OFFLINE');
    }
    setLastChecked(new Date());
  }, []);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, intervalMs);
    return () => clearInterval(interval);
  }, [checkHealth, intervalMs]);

  return { status, healthData, lastChecked, checkNow: checkHealth };
}
