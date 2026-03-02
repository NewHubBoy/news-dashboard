'use client';

import { useState, useEffect } from 'react';
import SearchForm from '@/components/SearchForm';
import NewsList from '@/components/NewsList';
import AIAnalysis from '@/components/AIAnalysis';
import {
  searchStockNews,
  analyzeNewsStream,
  getSearchedStocks,
  getStockHistory,
  getStockAnalysis,
  NewsArticle,
  IntegratedSearchResponse,
  SearchedStock,
} from '@/services/api';

interface AgentStep {
  step: number;
  total: number;
  message: string;
}

// 清理 AI 分析结果中的无用标签
const cleanAnalysisResult = (text: string | null): string | null => {
  if (!text) return null;
  let cleaned = text.trim();
  // 移除末尾常见的无用标签或词汇
  const unwantedSuffixes = ['\n分析', '\n分析。', '分析。', '分析', '\n总结', '\n总结。', '总结。', '总结'];
  for (const suffix of unwantedSuffixes) {
    if (cleaned.endsWith(suffix)) {
      cleaned = cleaned.slice(0, -suffix.length).trim();
      break;
    }
  }
  return cleaned;
};

export default function Home() {
  const [selectedStock, setSelectedStock] = useState<SearchedStock | null>(null);
  const [stockList, setStockList] = useState<SearchedStock[]>([]);
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [searchData, setSearchData] = useState<IntegratedSearchResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isAnalysisLoading, setIsAnalysisLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<string | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [analysisCached, setAnalysisCached] = useState(false);
  const [analysisUpdatedAt, setAnalysisUpdatedAt] = useState<string | null>(null);
  const [agentSteps, setAgentSteps] = useState<AgentStep[]>([]);

  // Load stock list on mount
  useEffect(() => {
    loadStockList();
  }, []);

  const loadStockList = async () => {
    try {
      const stocks = await getSearchedStocks();
      setStockList(stocks);
    } catch (err) {
      console.error('Failed to load stock list:', err);
    }
  };

  const handleSearch = async (stockCode: string, stockName: string) => {
    setIsLoading(true);
    setError(null);
    setAnalysisResult(null);
    setAnalysisError(null);
    setSearchData(null);
    setAnalysisCached(false);
    setAnalysisUpdatedAt(null);
    setAgentSteps([]);
    setSelectedStock({ stock_code: stockCode, stock_name: stockName, last_searched: new Date().toISOString() });

    try {
      const response = await searchStockNews({
        stock_code: stockCode,
        stock_name: stockName,
      });
      setArticles(response.articles);
      setSearchData(response);

      // Refresh stock list to include the new search
      await loadStockList();

      // Start AI Analysis automatically after fetching news (streaming)
      if (response.articles.length > 0) {
        setIsAnalysisLoading(true);
        setAgentSteps([]);
        try {
          await analyzeNewsStream(
            {
              stock_code: stockCode,
              stock_name: stockName,
              articles: response.articles,
              announcements: response.announcements,
              disclosures: response.disclosures,
              reports: response.reports,
              financial_data: response.financial_data,
            },
            {
              onStatus: (data) => setAgentSteps(prev => {
                const exists = prev.find(s => s.step === data.step && s.message === data.message);
                return exists ? prev : [...prev, data];
              }),
              onResult: (data) => {
                setAnalysisResult(cleanAnalysisResult(data.analysis_result));
                setAnalysisCached(data.cached);
                setAnalysisUpdatedAt(new Date().toISOString());
              },
              onError: (err) => setAnalysisError(err),
            }
          );
        } catch (aiErr) {
          setAnalysisError(aiErr instanceof Error ? aiErr.message : 'AI分析失败');
        } finally {
          setIsAnalysisLoading(false);
        }
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : '搜索失败，请稍后重试');
      setArticles([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectStock = async (stock: SearchedStock) => {
    setSelectedStock(stock);
    setIsLoading(true);
    setError(null);
    setAnalysisError(null);
    setAnalysisCached(true);

    try {
      // Load cached data from database
      const [history, analysis] = await Promise.all([
        getStockHistory(stock.stock_code),
        getStockAnalysis(stock.stock_code).catch(() => null),
      ]);

      setArticles(history.articles);
      setSearchData(history);

      if (analysis) {
        setAnalysisResult(cleanAnalysisResult(analysis.analysis_result));
        setAnalysisUpdatedAt(analysis.created_at);
      } else {
        setAnalysisResult(null);
        setAnalysisUpdatedAt(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载数据失败');
      setArticles([]);
      setSearchData(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefresh = async () => {
    if (!selectedStock) return;

    setIsRefreshing(true);
    setError(null);
    setAnalysisError(null);
    setAnalysisCached(false);

    try {
      const response = await searchStockNews({
        stock_code: selectedStock.stock_code,
        stock_name: selectedStock.stock_name,
      });
      setArticles(response.articles);
      setSearchData(response);

      // Refresh AI analysis (bypass cache, streaming)
      if (response.articles.length > 0) {
        setIsAnalysisLoading(true);
        setAgentSteps([]);
        try {
          await analyzeNewsStream(
            {
              stock_code: selectedStock.stock_code,
              stock_name: selectedStock.stock_name,
              articles: response.articles,
              announcements: response.announcements,
              disclosures: response.disclosures,
              reports: response.reports,
              financial_data: response.financial_data,
              bypass_cache: true,
            },
            {
              onStatus: (data) => setAgentSteps(prev => {
                const exists = prev.find(s => s.step === data.step && s.message === data.message);
                return exists ? prev : [...prev, data];
              }),
              onResult: (data) => {
                setAnalysisResult(cleanAnalysisResult(data.analysis_result));
                setAnalysisCached(data.cached);
                setAnalysisUpdatedAt(new Date().toISOString());
              },
              onError: (err) => setAnalysisError(err),
            }
          );
        } catch (aiErr) {
          setAnalysisError(aiErr instanceof Error ? aiErr.message : 'AI分析失败');
        } finally {
          setIsAnalysisLoading(false);
        }
      }

      // Update stock list
      await loadStockList();

    } catch (err) {
      setError(err instanceof Error ? err.message : '刷新失败');
    } finally {
      setIsRefreshing(false);
    }
  };

  const formatLastSearched = (dateStr: string | null) => {
    if (!dateStr) return '未知';
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return '刚刚';
    if (diffMins < 60) return `${diffMins}分钟前`;
    if (diffHours < 24) return `${diffHours}小时前`;
    return `${diffDays}天前`;
  };

  return (
    <main className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">
            股票新闻资讯看板
          </h1>
          <div className="flex items-center gap-4">
            {selectedStock && (
              <button
                onClick={handleRefresh}
                disabled={isRefreshing}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 text-sm"
                title="重新获取最新数据，包括AI分析"
              >
                {isRefreshing ? (
                  <>
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    刷新中...
                  </>
                ) : (
                  <>
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    强制刷新
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-64 bg-white border-r border-gray-200 overflow-y-auto">
          <div className="p-4">
            <SearchForm onSearch={handleSearch} isLoading={isLoading} />
          </div>

          <div className="border-t border-gray-200">
            <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
              <h2 className="text-sm font-semibold text-gray-700">搜索历史</h2>
            </div>
            <ul className="divide-y divide-gray-100">
              {stockList.length === 0 ? (
                <li className="px-4 py-8 text-center text-gray-400 text-sm">
                  暂无搜索记录
                </li>
              ) : (
                stockList.map((stock) => (
                  <li key={stock.stock_code}>
                    <button
                      onClick={() => handleSelectStock(stock)}
                      className={`w-full px-4 py-3 text-left hover:bg-gray-50 transition-colors ${selectedStock?.stock_code === stock.stock_code
                        ? 'bg-blue-50 border-l-4 border-blue-600'
                        : ''
                        }`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium text-gray-900">{stock.stock_name}</div>
                          <div className="text-sm text-gray-500">{stock.stock_code}</div>
                        </div>
                        <div className="text-xs text-gray-400">
                          {formatLastSearched(stock.last_searched)}
                        </div>
                      </div>
                    </button>
                  </li>
                ))
              )}
            </ul>
          </div>
        </aside>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto">
          <div className="container mx-auto max-w-5xl py-6 px-4">
            {!selectedStock ? (
              <div className="flex flex-col items-center justify-center h-full min-h-[400px] text-gray-400">
                <svg className="w-16 h-16 mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <p className="text-lg">请选择或搜索一只股票查看资讯</p>
              </div>
            ) : (
              <>
                <div className="mb-6">
                  <h2 className="text-xl font-semibold text-gray-900">
                    {selectedStock.stock_name} ({selectedStock.stock_code})
                  </h2>
                </div>

                <AIAnalysis
                  isLoading={isAnalysisLoading}
                  error={analysisError}
                  result={analysisResult}
                  cached={analysisCached}
                  updatedAt={analysisUpdatedAt ?? undefined}
                  agentSteps={agentSteps}
                />

                <NewsList
                  articles={articles}
                  announcements={searchData?.announcements || []}
                  disclosures={searchData?.disclosures || []}
                  reports={searchData?.reports || []}
                  financial_data={searchData?.financial_data || []}
                  isLoading={isLoading}
                  error={error}
                />
              </>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
