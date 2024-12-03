import axios from 'axios';
import { WebhookConfig, CreateWebhookRequest, UpdateWebhookRequest } from './types';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const BASE_URL = `${API_URL}/api/webhooks`;

export const webhookApi = {
  getWebhooks: async (): Promise<WebhookConfig[]> => {
    const response = await axios.get(BASE_URL);
    return response.data;
  },

  getWebhook: async (id: number): Promise<WebhookConfig> => {
    const response = await axios.get(`${BASE_URL}/${id}`);
    return response.data;
  },

  createWebhook: async (webhook: CreateWebhookRequest): Promise<WebhookConfig> => {
    const response = await axios.post(BASE_URL, webhook);
    return response.data;
  },

  updateWebhook: async (id: number, webhook: UpdateWebhookRequest): Promise<WebhookConfig> => {
    const response = await axios.put(`${BASE_URL}/${id}`, webhook);
    return response.data;
  },

  deleteWebhook: async (id: number): Promise<void> => {
    await axios.delete(`${BASE_URL}/${id}`);
  },

  testWebhook: async (id: number): Promise<void> => {
    await axios.post(`${BASE_URL}/${id}/test`);
  }
};
