import { api } from './client';
import { LiveMetrics, FullMetrics } from '../types';

export const metricsApi = {
  getLive: () => api.get<LiveMetrics>('/metrics/live'),
  getFull: () => api.get<FullMetrics>('/metrics/'),
};
