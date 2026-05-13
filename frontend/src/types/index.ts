export interface Product {
  id: number;
  category: string;
  subcategory: string | null;
  brand: string;
  model: string;
  specs: Record<string, unknown>;
  release_date: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface PriceHistory {
  id: number;
  product_id: number;
  source: string;
  price: number;
  date: string;
}

export interface CostEstimate {
  id: number;
  product_id: number;
  materials_cost: number;
  logistics_cost: number;
  labor_cost: number;
  total: number;
  last_updated: string | null;
}

export interface ReviewQuality {
  id: number;
  product_id: number;
  avg_rating: number | null;
  defect_rate: number | null;
  reviews_count: number | null;
  source: string | null;
  last_updated: string | null;
}

export interface PopularityStats {
  id: number;
  product_id: number;
  daily_views: number;
  total_views: number;
  daily_searches: number;
  last_updated: string | null;
}

export interface ProductFull extends Product {
  price_history: PriceHistory[];
  cost_estimate: CostEstimate | null;
  review_quality: ReviewQuality | null;
  popularity_stats: PopularityStats | null;
}

export interface ProductWithMarkup extends Product {
  price_history: PriceHistory[];
  cost_estimate: CostEstimate | null;
  review_quality: ReviewQuality | null;
  popularity_stats: PopularityStats | null;
  market_price: number | null;
  markup_percent: number | null;
  adjusted_markup: number | null;
  markup_status: string | null;
}

export interface SearchResult {
  total: number;
  page: number;
  per_page: number;
  items: ProductWithMarkup[];
}

export interface AlternativeProduct {
  product_id: number;
  brand: string;
  model: string;
  price: number;
  quality_factor: number;
  markup_percent: number;
  score: number;
  recommendation: string;
}

export interface AlternativesResponse {
  product_id: number;
  category: string;
  alternatives_count: number;
  alternatives: AlternativeProduct[];
}

export interface DailyProductItem {
  product: Product;
  daily_views: number;
  avg_price: number;
}

export interface DailyProductsResponse {
  date: string;
  products: DailyProductItem[];
}

export interface PricePrediction {
  current_price: number;
  predicted_1m: number | null;
  predicted_3m: number | null;
  trend: string | null;
  recommendation: string | null;
  confidence: number | null;
  last_updated: string | null;
}

export interface ProductFull extends Product {
  price_history: PriceHistory[];
  cost_estimate: CostEstimate | null;
  review_quality: ReviewQuality | null;
  popularity_stats: PopularityStats | null;
  price_prediction: PricePrediction | null;
}
