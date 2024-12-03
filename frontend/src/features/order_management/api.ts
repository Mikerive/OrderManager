import axios from 'axios';
import { Order, CreateOrderRequest } from './types';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const BASE_URL = `${API_URL}/api/orders`;

export const ordersApi = {
  getOrders: async (): Promise<Order[]> => {
    const response = await axios.get(BASE_URL);
    return response.data;
  },

  getOrder: async (id: number): Promise<Order> => {
    const response = await axios.get(`${BASE_URL}/${id}`);
    return response.data;
  },

  createOrder: async (order: CreateOrderRequest): Promise<Order> => {
    const response = await axios.post(BASE_URL, order);
    return response.data;
  },

  updateOrder: async (id: number, order: Partial<CreateOrderRequest>): Promise<Order> => {
    const response = await axios.put(`${BASE_URL}/${id}`, order);
    return response.data;
  },

  cancelOrder: async (id: number): Promise<void> => {
    await axios.post(`${BASE_URL}/${id}/cancel`);
  },

  deleteOrder: async (id: number): Promise<void> => {
    await axios.delete(`${BASE_URL}/${id}`);
  },

  // Chain-related operations
  createOrderChain: async (orders: CreateOrderRequest[]): Promise<Order[]> => {
    const response = await axios.post(`${BASE_URL}/chain`, { orders });
    return response.data;
  },

  createBracketOrder: async (
    entry: CreateOrderRequest,
    takeProfit: CreateOrderRequest,
    stopLoss: CreateOrderRequest
  ): Promise<Order[]> => {
    const response = await axios.post(`${BASE_URL}/bracket`, {
      entry_order: entry,
      take_profit: takeProfit,
      stop_loss: stopLoss
    });
    return response.data;
  },

  createOCOOrder: async (
    limitOrder: CreateOrderRequest,
    stopOrder: CreateOrderRequest
  ): Promise<Order[]> => {
    const response = await axios.post(`${BASE_URL}/oco`, {
      limit_order: limitOrder,
      stop_order: stopOrder
    });
    return response.data;
  }
};
