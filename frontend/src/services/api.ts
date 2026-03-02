const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface StockSearchRequest {
  stock_code: string;
  stock_name: string;
}

export interface NewsArticle {
  id?: number;
  stock_code: string;
  stock_name: string;
  title: string;
  description?: string;
  url: string;
  source: string;
  published_at?: string;
}

export interface FinancialDocument {
  id?: number;
  stock_code: string;
  stock_name: string;
  doc_type: string;
  title: string;
  content_summary?: string;
  url: string;
  source: string;
  published_at?: string;
}

export interface IntegratedSearchResponse {
  articles: NewsArticle[];
  announcements: FinancialDocument[];
  disclosures: FinancialDocument[];
  reports: FinancialDocument[];
  financial_data: FinancialDocument[];
  total_news: number;
}

export interface AgentAnalyzeRequest {
  stock_code: string;
  stock_name: string;
  articles: NewsArticle[];
  announcements: FinancialDocument[];
  disclosures: FinancialDocument[];
  reports: FinancialDocument[];
  financial_data: FinancialDocument[];
  bypass_cache?: boolean;
}

export interface AgentAnalyzeResponse {
  analysis_result: string;
  cached: boolean;
}

export const searchStockNews = async (request: StockSearchRequest): Promise<IntegratedSearchResponse> => {
  const response = await fetch(`${API_BASE_URL}/api/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch data');
  }

  return response.json();
};

export const getStockNewsHistory = async (stockCode: string): Promise<IntegratedSearchResponse> => {
  const response = await fetch(`${API_BASE_URL}/api/news/${stockCode}`);

  if (!response.ok) {
    throw new Error('Failed to fetch history');
  }

  return response.json();
};

export const analyzeNews = async (request: AgentAnalyzeRequest): Promise<AgentAnalyzeResponse> => {
  const response = await fetch(`${API_BASE_URL}/api/agent/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch AI analysis');
  }

  return response.json();
};

export interface SearchedStock {
  stock_code: string;
  stock_name: string;
  last_searched: string | null;
}

export const getSearchedStocks = async (): Promise<SearchedStock[]> => {
  const response = await fetch(`${API_BASE_URL}/api/stocks`);

  if (!response.ok) {
    throw new Error('Failed to fetch searched stocks');
  }

  return response.json();
};

export const getStockHistory = async (stockCode: string): Promise<IntegratedSearchResponse> => {
  const response = await fetch(`${API_BASE_URL}/api/history/${stockCode}`);

  if (!response.ok) {
    throw new Error('Failed to fetch stock history');
  }

  return response.json();
};

export interface StockAnalysis {
  analysis_result: string;
  created_at: string;
}

export const getStockAnalysis = async (stockCode: string): Promise<StockAnalysis> => {
  const response = await fetch(`${API_BASE_URL}/api/analysis/${stockCode}`);

  if (!response.ok) {
    throw new Error('Failed to fetch stock analysis');
  }

  return response.json();
};
