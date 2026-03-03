'use client';

import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

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
      <h3 className="text-sm font-semibold mb-3">添加股票</h3>

      <div className="space-y-3">
        <div>
          <Input
            type="text"
            value={stockCode}
            onChange={(e) => setStockCode(e.target.value)}
            placeholder="股票代码 (如: 600089)"
            disabled={isLoading}
          />
        </div>

        <div>
          <Input
            type="text"
            value={stockName}
            onChange={(e) => setStockName(e.target.value)}
            placeholder="股票名称 (如: 特变电工)"
            disabled={isLoading}
          />
        </div>

        <Button
          type="submit"
          disabled={isLoading || !stockCode.trim() || !stockName.trim()}
          className="w-full"
        >
          {isLoading ? '搜索中...' : '搜索'}
        </Button>
      </div>
    </form>
  );
}
