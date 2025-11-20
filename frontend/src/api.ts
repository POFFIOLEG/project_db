import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export const fetchList = async <T>(endpoint: string): Promise<T[]> => {
  const { data } = await apiClient.get(endpoint);
  if (Array.isArray(data)) {
    return data;
  }
  return (data.results as T[]) ?? [];
};

export const createItem = async <T>(endpoint: string, payload: T) => {
  const { data } = await apiClient.post(endpoint, payload);
  return data;
};

