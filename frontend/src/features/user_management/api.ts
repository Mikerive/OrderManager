import axios from 'axios';
import { User, LoginRequest, RegisterRequest, LoginResponse, UpdateUserRequest } from './types';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const BASE_URL = `${API_URL}/api/users`;

export const userApi = {
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    const response = await axios.post(`${BASE_URL}/login`, credentials);
    return response.data;
  },

  register: async (userData: RegisterRequest): Promise<User> => {
    const response = await axios.post(`${BASE_URL}/register`, userData);
    return response.data;
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await axios.get(`${BASE_URL}/me`);
    return response.data;
  },

  updateUser: async (userId: number, userData: UpdateUserRequest): Promise<User> => {
    const response = await axios.put(`${BASE_URL}/${userId}`, userData);
    return response.data;
  },

  deleteUser: async (userId: number): Promise<void> => {
    await axios.delete(`${BASE_URL}/${userId}`);
  },

  logout: async (): Promise<void> => {
    await axios.post(`${BASE_URL}/logout`);
  }
};
