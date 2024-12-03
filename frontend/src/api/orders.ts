import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface Order {
  id: number;
  title: string;
  description?: string;
  status: string;
  symbol: string;
  quantity: number;
  order_type: string;
  side: string;
  price?: number;
  provider: string;
  created_at: string;
  updated_at: string;
}

export interface CreateOrderRequest {
  title: string;
  description?: string;
  symbol: string;
  quantity: number;
  order_type: string;
  side: string;
  price?: number;
  provider: string;
}

export const ordersApi = {
  getOrders: async (): Promise<Order[]> => {
    const response = await axios.get(`${API_URL}/api/orders`);
    return response.data;
  },

  getOrder: async (id: number): Promise<Order> => {
    const response = await axios.get(`${API_URL}/api/orders/${id}`);
    return response.data;
  },

  createOrder: async (order: CreateOrderRequest): Promise<Order> => {
    const response = await axios.post(`${API_URL}/api/orders`, order);
    return response.data;
  },

  cancelOrder: async (id: number): Promise<void> => {
    await axios.post(`${API_URL}/api/orders/${id}/cancel`);
  }
};
