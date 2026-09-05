import { api } from './client';

export interface SimulateWebhookRequest {
  event_type: string;
  amount: number;
  currency?: string;
  merchant_id?: string;
  customer_id?: string;
  reference_id?: string;
  custom_payload?: any;
}

export interface SimulateWebhookResponse {
  webhook_event: string;
  mapped_event_type: string;
  ingest_status: string;
  case_id: string | null;
  workflow_result: any;
  simulated_payload: any;
}

export const razorpayApi = {
  simulateWebhook: (data: SimulateWebhookRequest) =>
    api.post<SimulateWebhookResponse>('/razorpay/simulate-webhook', data),
};
