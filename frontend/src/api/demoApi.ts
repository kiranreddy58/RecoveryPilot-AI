import { api } from './client';
import { DemoResult, BatchRun, BatchResults } from '../types';

export const demoApi = {
  runScenario: (scenario: number) =>
    api.post<DemoResult>(`/demo/run?scenario=${scenario}`),

  runAll: () => api.post<Array<{ scenario: number; result: any }>>('/demo/run-all'),
};

export const batchApi = {
  runBatch: (target_count: number) =>
    api.post<any>('/batch/run', { target_count }),

  listBatches: () => api.get<BatchRun[]>('/batch/'),

  getBatchResults: (batch_id: string) =>
    api.get<BatchResults>(`/batch/${batch_id}/results`),
};
