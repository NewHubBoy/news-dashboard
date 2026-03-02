import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface AIAnalysisProps {
    isLoading: boolean;
    error: string | null;
    result: string | null;
    cached?: boolean;
    updatedAt?: string;
}

export default function AIAnalysis({ isLoading, error, result, cached, updatedAt }: AIAnalysisProps) {
    if (!isLoading && !error && !result) {
        return null;
    }

    // 清理 AI 输出中的无用标签和格式问题，保留 Markdown 格式
    const cleanResult = (text: string): string => {
        let cleaned = text.trim();

        // 尝试找到报告真正开始的位置（以 ### 1. 开头）
        const reportStartPatterns = [
            /###\s*1\s*[.、]\s*核心事件/,
            /##\s*1\s*[.、]\s*核心事件/,
            /#{1,3}\s*1\s*[.、]\s*核心事件/,
            /#{1,3}\s*核心事件/,
        ];

        for (const pattern of reportStartPatterns) {
            const match = cleaned.match(pattern);
            if (match && match.index !== undefined) {
                // 从真正报告开始的位置截取，保留所有 Markdown 格式
                cleaned = cleaned.slice(match.index);
                break;
            }
        }

        // 清理开头的无用标签（只清理纯标签，不破坏 Markdown）
        const startTagPatterns = [
            /^[分析总结评估建议备注说明报告结果]+[：:：]\s*\n?/,  // "分析：" 或 "分析:" 开头
            /^[分析总结评估建议备注说明报告结果]+\s*\n?/,          // 纯标签开头
        ];

        for (const pattern of startTagPatterns) {
            const match = cleaned.match(pattern);
            if (match) {
                cleaned = cleaned.slice(match[0].length);
                break;
            }
        }

        // 清理结尾的无用标签（只检查最后一行）
        const lines = cleaned.split('\n');
        if (lines.length > 0) {
            const lastLine = lines[lines.length - 1].trim();

            // 如果最后一行是纯标签（不包含 Markdown 内容），移除它
            const tagPatterns = [
                /^[分析总结评估建议备注说明]+[。。，、；：,;]?$/,  // 纯标签+可选标点
                /^[分析总结评估建议备注说明]+$/,                   // 纯标签
            ];

            if (lastLine && tagPatterns.some(pattern => pattern.test(lastLine))) {
                lines.pop();
                cleaned = lines.join('\n').trim();
            }
        }

        return cleaned;
    };

    const formatUpdatedTime = (dateStr: string) => {
        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);

        if (diffMins < 1) return '刚刚';
        if (diffMins < 60) return `${diffMins}分钟前`;
        if (diffHours < 24) return `${diffHours}小时前`;
        return date.toLocaleDateString('zh-CN');
    };

    return (
        <div className="bg-white rounded-lg shadow-md p-6 mb-8 border border-blue-100">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                    </div>
                    <h2 className="text-xl font-bold text-gray-800">AI 投资分析</h2>
                </div>

                {result && !isLoading && (
                    <div className="flex items-center gap-2 text-xs">
                        {cached && (
                            <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded-full">
                                来自缓存
                            </span>
                        )}
                        {updatedAt && (
                            <span className="text-gray-400">
                                {formatUpdatedTime(updatedAt)}
                            </span>
                        )}
                    </div>
                )}
            </div>

            {isLoading && (
                <div className="flex flex-col items-center justify-center py-8">
                    <div className="w-10 h-10 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mb-4"></div>
                    <p className="text-gray-500">正在分析最新数据，生成专业投资建议...</p>
                </div>
            )}

            {error && (
                <div className="p-4 bg-red-50 text-red-600 rounded-md">
                    <p className="font-semibold">分析出错</p>
                    <p className="text-sm mt-1">{error}</p>
                </div>
            )}

            {result && !isLoading && (
                <div className="prose prose-blue max-w-none prose-headings:text-gray-800 prose-p:text-gray-600 prose-strong:text-gray-900 prose-code:text-pink-600 prose-pre:bg-gray-100 mt-4">
                    <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                            // 自定义标题样式
                            h1: ({ children }) => <h1 className="text-xl font-bold text-gray-900 mb-4">{children}</h1>,
                            h2: ({ children }) => <h2 className="text-lg font-semibold text-gray-800 mb-3 mt-6">{children}</h2>,
                            h3: ({ children }) => <h3 className="text-base font-semibold text-gray-800 mb-2 mt-4">{children}</h3>,
                            h4: ({ children }) => <h4 className="text-sm font-semibold text-gray-800 mb-2 mt-3">{children}</h4>,
                            // 自定义段落样式
                            p: ({ children }) => <p className="text-gray-700 mb-3 leading-relaxed">{children}</p>,
                            // 自定义列表样式
                            ul: ({ children }) => (
                                <ul className="list-disc list-inside space-y-1.5 mb-4 text-gray-700 [&_li>p]:inline [&_li>p]:m-0">{children}</ul>
                            ),
                            ol: ({ children }) => (
                                <ol className="list-decimal list-inside space-y-1.5 mb-4 text-gray-700 [&_li>p]:inline [&_li>p]:m-0">{children}</ol>
                            ),
                            li: ({ children }) => (
                                <li className="leading-relaxed">{children}</li>
                            ),
                            // 自定义强调样式
                            strong: ({ children }) => <strong className="font-semibold text-gray-900">{children}</strong>,
                            em: ({ children }) => <em className="italic text-gray-700">{children}</em>,
                            // 自定义代码样式
                            code: ({ children, className }) => {
                                const isInline = !className;
                                return isInline ? (
                                    <code className="bg-gray-100 text-pink-600 px-1 py-0.5 rounded text-sm font-mono">{children}</code>
                                ) : (
                                    <code className={className}>{children}</code>
                                );
                            },
                            // 自定义引用样式
                            blockquote: ({ children }) => (
                                <blockquote className="border-l-4 border-blue-500 pl-4 italic text-gray-600 my-4">{children}</blockquote>
                            ),
                        }}
                    >
                        {cleanResult(result)}
                    </ReactMarkdown>
                </div>
            )}
        </div>
    );
}
