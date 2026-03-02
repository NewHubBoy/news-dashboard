'use client';

import { useState } from 'react';

interface SearchFormProps {
  onSearch: (stockCode: string, stockName: string) => void;
  isLoading: boolean;
}

export default function SearchForm({ onSearch, isLoading }: SearchFormProps) {
  const [stockCode, setStockCode] = useState('');
  const [stockName, setStockName] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (stockCode.trim() && stockName.trim()) {
      onSearch(stockCode.trim(), stockName.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">添加股票</h3>

      <div className="space-y-3">
        <div>
          <input
            type="text"
            value={stockCode}
            onChange={(e) => setStockCode(e.target.value)}
            placeholder="股票代码 (如: 600089)"
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading}
          />
        </div>

        <div>
          <input
            type="text"
            value={stockName}
            onChange={(e) => setStockName(e.target.value)}
            placeholder="股票名称 (如: 特变电工)"
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading}
          />
        </div>

        <button
          type="submit"
          disabled={isLoading || !stockCode.trim() || !stockName.trim()}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md text-sm hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? '搜索中...' : '搜索'}
        </button>
      </div>
    </form>
  );
}
