import api from './client';
import type {
  Product,
  ProductFull,
  SearchResult,
  AlternativesResponse,
  DailyProductsResponse,
} from '../types';

export const productsApi = {
  getAll: (category?: string, subcategory?: string, skip = 0, limit = 20) =>
    api.get<Product[]>('/products/', { params: { category, subcategory, skip, limit } }),

  getById: (id: number) =>
    api.get<ProductFull>(`/products/${id}`),

  search: (query: string, params?: {
    category?: string;
    subcategory?: string;
    brand?: string;
    min_price?: number;
    max_price?: number;
    page?: number;
    per_page?: number;
  }) =>
    api.get<SearchResult>('/search', { params: { query, ...params } }),

  getAlternatives: (product_id: number, category: string, max_count = 5) =>
    api.post<AlternativesResponse>('/alternatives', { product_id, category, max_count }),

  getDaily: (top_n = 5) =>
    api.get<DailyProductsResponse>('/daily', { params: { top_n } }),

  trackView: (productId: number) =>
    api.post(`/daily/track-view/${productId}`),
};
