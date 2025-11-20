export type PriceType = 'regular' | 'markdown' | 'promo';

export interface Product {
  id: number;
  name: string;
  sku: string;
  barcode: string;
  category: string;
  unit: string;
  shelf_life_days: number;
}

export interface Supplier {
  id: number;
  name: string;
  phone?: string;
  email?: string;
}

export interface StockItem {
  id: number;
  product: Product;
  quantity: string;
  stock_area: number;
  expiration_date: string;
}

export interface PriceListItem {
  id: number;
  product: number;
  product_name: string;
  price_type: PriceType;
  final_price: string;
  input_price: string;
  label_type: string;
  trading_point: string;
  reason: string;
}

export interface Employee {
  id: number;
  full_name: string;
  status: string;
  position: number | null;
  department: number | null;
}

export interface AttendanceReport {
  id: number;
  week_start: string;
  week_end: string;
  comment: string;
}

