'use client';

import { NewsArticle, FinancialDocument } from '@/services/api';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

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
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTitle>错误</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (articles.length === 0 && announcements.length === 0) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p>暂无新闻或市场数据，请输入股票代码进行搜索</p>
      </div>
    );
  }

  const renderSection = (title: string, items: any[], type: 'news' | 'doc', sectionPrefix: string) => {
    if (!items || items.length === 0) return null;

    return (
      <div className="mb-10">
        <h3 className="text-xl font-bold mb-4 border-b pb-2">
          {title} <span className="text-sm font-normal text-muted-foreground ml-2">({items.length}条)</span>
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {items.map((item, index) => (
            <Card
              key={`${sectionPrefix}-${item.url?.replace(/[^a-zA-Z0-9]/g, '') || index}-${index}`}
              className="hover:shadow-md transition-shadow"
            >
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="h-full flex flex-col"
              >
                <CardHeader className="pb-3">
                  <CardTitle className="text-md hover:text-primary line-clamp-2">
                    {item.title}
                  </CardTitle>
                </CardHeader>

                {(type === 'news' ? item.description : item.content_summary) && (
                  <CardContent className="pb-3 grow">
                    <CardDescription className="line-clamp-3">
                      {type === 'news' ? item.description : item.content_summary}
                    </CardDescription>
                  </CardContent>
                )}

                <CardFooter className="pt-2 text-xs text-muted-foreground border-t">
                  <div className="flex items-center justify-between w-full">
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
                </CardFooter>
              </a>
            </Card>
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
