export interface Order {
  id: number;
  title: string;
  description?: string;
  status: OrderStatus;
  symbol: string;
  quantity: number;
  order_type: OrderType;
  side: OrderSide;
  price?: number;
  stop_price?: number;
  limit_price?: number;
  provider: string;
  provider_order_id?: string;
  chain_id?: string;
  chain_type?: string;
  chain_sequence?: number;
  parent_order_id?: number;
  created_at: string;
  updated_at: string;
}

export enum OrderStatus {
  PENDING = 'pending',
  ACTIVE = 'active',
  FILLED = 'filled',
  CANCELLED = 'cancelled',
  FAILED = 'failed'
}

export enum OrderType {
  MARKET = 'market',
  LIMIT = 'limit',
  STOP = 'stop',
  STOP_LIMIT = 'stop_limit'
}

export enum OrderSide {
  BUY = 'buy',
  SELL = 'sell'
}

export interface CreateOrderRequest {
  title: string;
  description?: string;
  symbol: string;
  quantity: number;
  order_type: OrderType;
  side: OrderSide;
  price?: number;
  stop_price?: number;
  limit_price?: number;
  provider: string;
  chain_id?: string;
  chain_type?: string;
  chain_sequence?: number;
  parent_order_id?: number;
}

export interface OrderEdge {
  from_order_id: number;
  to_order_id: number;
  condition_type: string;
  condition_data: Record<string, any>;
}
