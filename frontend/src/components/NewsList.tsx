'use client';

import { NewsArticle, FinancialDocument } from '@/services/api';

interface NewsListProps {
  articles: NewsArticle[];
  announcements: FinancialDocument[];
  disclosures: FinancialDocument[];
  reports: FinancialDocument[];
  financial_data: FinancialDocument[];
  isLoading: boolean;
  error: string | null;
}

export default function NewsList({
  articles,
  announcements,
  disclosures,
  reports,
  financial_data,
  isLoading,
  error
}: NewsListProps) {
  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        <p className="font-medium">错误</p>
        <p className="text-sm">{error}</p>
      </div>
    );
  }

  if (articles.length === 0 && announcements.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>暂无新闻或市场数据，请输入股票代码进行搜索</p>
      </div>
    );
  }

  const renderSection = (title: string, items: any[], type: 'news' | 'doc', sectionPrefix: string) => {
    if (!items || items.length === 0) return null;

    return (
      <div className="mb-10">
        <h3 className="text-xl font-bold mb-4 text-gray-800 border-b pb-2">
          {title} <span className="text-sm font-normal text-gray-500 ml-2">({items.length}条)</span>
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {items.map((item, index) => (
            <div
              key={`${sectionPrefix}-${item.url?.replace(/[^a-zA-Z0-9]/g, '') || index}-${index}`}
              className="bg-white rounded-lg shadow-sm border border-gray-100 p-5 hover:shadow-md transition-shadow"
            >
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="h-full flex flex-col"
              >
                <h4 className="text-md font-semibold text-gray-900 mb-2 hover:text-blue-600 line-clamp-2">
                  {item.title}
                </h4>

                {(type === 'news' ? item.description : item.content_summary) && (
                  <p className="text-gray-600 text-sm mb-3 line-clamp-3 grow">
                    {type === 'news' ? item.description : item.content_summary}
                  </p>
                )}

                <div className="flex items-center justify-between text-xs text-gray-500 mt-auto pt-2 border-t border-gray-50">
                  <span className="font-medium truncate max-w-[120px]" title={item.source}>{item.source}</span>
                  {item.published_at && (
                    <span className="shrink-0 ml-2">
                      {new Date(item.published_at).toLocaleDateString('zh-CN', {
                        month: 'short',
                        day: 'numeric',
                      })}
                    </span>
                  )}
                </div>
              </a>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="w-full mx-auto space-y-8">
      {renderSection("📰 最新资讯", articles, "news", "articles")}
      {renderSection("📢 交易所公告", announcements, "doc", "announcements")}
      {renderSection("📑 监管披露", disclosures, "doc", "disclosures")}
      {renderSection("📊 券商研报", reports, "doc", "reports")}
      {renderSection("📈 行情与财务数据", financial_data, "doc", "financial")}
    </div>
  );
}
