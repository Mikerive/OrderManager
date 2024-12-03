export interface WebhookConfig {
  id: number;
  name: string;
  url: string;
  events: WebhookEvent[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export enum WebhookEvent {
  ORDER_CREATED = 'order_created',
  ORDER_UPDATED = 'order_updated',
  ORDER_CANCELLED = 'order_cancelled',
  ORDER_FILLED = 'order_filled',
  ORDER_FAILED = 'order_failed',
}

export interface CreateWebhookRequest {
  name: string;
  url: string;
  events: WebhookEvent[];
}

export interface UpdateWebhookRequest {
  name?: string;
  url?: string;
  events?: WebhookEvent[];
  is_active?: boolean;
}
