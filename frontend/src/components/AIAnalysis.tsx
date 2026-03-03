import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Zap } from 'lucide-react';

interface AgentStep {
    step: number;
    total: number;
    message: string;
}

interface AIAnalysisProps {
    isLoading: boolean;
    error: string | null;
    result: string | null;
    cached?: boolean;
    updatedAt?: string;
    agentSteps?: AgentStep[];
}

export default function AIAnalysis({ isLoading, error, result, cached, updatedAt, agentSteps = [] }: AIAnalysisProps) {
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
                cleaned = cleaned.slice(match.index);
                break;
            }
        }

        const startTagPatterns = [
            /^[分析总结评估建议备注说明报告结果]+[：:：]\s*\n?/,
            /^[分析总结评估建议备注说明报告结果]+\s*\n?/,
        ];

        for (const pattern of startTagPatterns) {
            const match = cleaned.match(pattern);
            if (match) {
                cleaned = cleaned.slice(match[0].length);
                break;
            }
        }

        const lines = cleaned.split('\n');
        if (lines.length > 0) {
            const lastLine = lines[lines.length - 1].trim();
            const tagPatterns = [
                /^[分析总结评估建议备注说明]+[。。，、；：,;]?$/,
                /^[分析总结评估建议备注说明]+$/,
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

    // 全部四步的定义
    const allSteps = [
        { step: 1, label: '事实提取' },
        { step: 2, label: '深度分析' },
        { step: 3, label: '质量审查' },
        { step: 4, label: '报告生成' },
    ];

    const currentMaxStep = agentSteps.length > 0 ? Math.max(...agentSteps.map(s => s.step)) : 0;
    const latestMessage = agentSteps.length > 0 ? agentSteps[agentSteps.length - 1].message : '';

    return (
        <Card className="mb-8">
            <CardHeader>
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                            <Zap className="w-5 h-5" />
                        </div>
                        <CardTitle>AI 投资分析</CardTitle>
                    </div>

                    {result && !isLoading && (
                        <div className="flex items-center gap-2 text-xs">
                            {cached && (
                                <span className="px-2 py-1 bg-muted text-muted-foreground rounded-full">
                                    来自缓存
                                </span>
                            )}
                            {updatedAt && (
                                <span className="text-muted-foreground">
                                    {formatUpdatedTime(updatedAt)}
                                </span>
                            )}
                        </div>
                    )}
                </div>
            </CardHeader>

            <CardContent>
                {isLoading && (
                    <div className="py-4">
                        {/* 步骤进度条 */}
                        <div className="flex items-center gap-1 mb-5">
                            {allSteps.map((s, i) => {
                                const isCompleted = currentMaxStep > s.step;
                                const isCurrent = currentMaxStep === s.step;
                                return (
                                    <div key={s.step} className="flex items-center flex-1">
                                        <div className="flex flex-col items-center flex-1">
                                            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-all duration-500 ${isCompleted
                                                    ? 'bg-green-500 text-white'
                                                    : isCurrent
                                                        ? 'bg-primary text-primary-foreground animate-pulse'
                                                        : 'bg-muted text-muted-foreground'
                                                }`}>
                                                {isCompleted ? '✓' : s.step}
                                            </div>
                                            <span className={`text-xs mt-1 ${isCompleted ? 'text-green-600 dark:text-green-400' : isCurrent ? 'text-primary font-medium' : 'text-muted-foreground'
                                                }`}>
                                                {s.label}
                                            </span>
                                        </div>
                                        {i < allSteps.length - 1 && (
                                            <div className={`h-0.5 flex-1 mx-1 transition-all duration-500 ${isCompleted ? 'bg-green-400' : 'bg-muted'
                                                }`} />
                                        )}
                                    </div>
                                );
                            })}
                        </div>

                        {/* 当前状态消息 */}
                        {latestMessage ? (
                            <div className="flex items-center gap-3 p-3 bg-primary/10 rounded-lg">
                                <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin shrink-0"></div>
                                <span className="text-sm text-primary">{latestMessage}</span>
                            </div>
                        ) : (
                            <div className="flex items-center gap-3 p-3 bg-muted rounded-lg">
                                <div className="w-5 h-5 border-2 border-muted-foreground border-t-transparent rounded-full animate-spin shrink-0"></div>
                                <span className="text-sm text-muted-foreground">正在启动 AI Agent 分析流水线...</span>
                            </div>
                        )}

                        {/* 历史步骤日志 */}
                        {agentSteps.length > 1 && (
                            <div className="mt-3 space-y-1">
                                {agentSteps.slice(0, -1).map((s, i) => (
                                    <div key={i} className="flex items-center gap-2 text-xs text-muted-foreground">
                                        <span className="text-green-500 dark:text-green-400">✓</span>
                                        <span>{s.message}</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {error && (
                    <Alert variant="destructive">
                        <AlertDescription>
                            <p className="font-semibold">分析出错</p>
                            <p className="text-sm mt-1">{error}</p>
                        </AlertDescription>
                    </Alert>
                )}

                {result && !isLoading && (
                    <div className="prose prose-blue dark:prose-invert max-w-none prose-headings:text-foreground prose-p:text-foreground prose-strong:text-foreground prose-li:text-foreground prose-code:text-pink-600 dark:prose-code:text-pink-400 prose-pre:bg-muted mt-4">
                        <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                                // 自定义标题样式
                                h1: ({ children }) => <h1 className="text-xl font-bold text-foreground mb-4">{children}</h1>,
                                h2: ({ children }) => <h2 className="text-lg font-semibold text-foreground mb-3 mt-6">{children}</h2>,
                                h3: ({ children }) => <h3 className="text-base font-semibold text-foreground mb-2 mt-4">{children}</h3>,
                                h4: ({ children }) => <h4 className="text-sm font-semibold text-foreground mb-2 mt-3">{children}</h4>,
                                // 自定义段落样式
                                p: ({ children }) => <p className="text-foreground mb-3 leading-relaxed">{children}</p>,
                                // 自定义列表样式
                                ul: ({ children }) => (
                                    <ul className="list-disc list-inside space-y-1.5 mb-4 text-foreground [&_li>p]:inline [&_li>p]:m-0">{children}</ul>
                                ),
                                ol: ({ children }) => (
                                    <ol className="list-decimal list-inside space-y-1.5 mb-4 text-foreground [&_li>p]:inline [&_li>p]:m-0">{children}</ol>
                                ),
                                li: ({ children }) => (
                                    <li className="leading-relaxed">{children}</li>
                                ),
                                // 自定义强调样式
                                strong: ({ children }) => <strong className="font-semibold text-foreground">{children}</strong>,
                                em: ({ children }) => <em className="italic text-foreground">{children}</em>,
                                // 自定义代码样式
                                code: ({ children, className }) => {
                                    const isInline = !className;
                                    return isInline ? (
                                        <code className="bg-muted text-pink-600 dark:text-pink-400 px-1 py-0.5 rounded text-sm font-mono">{children}</code>
                                    ) : (
                                        <code className={className}>{children}</code>
                                    );
                                },
                                // 自定义引用样式
                                blockquote: ({ children }) => (
                                    <blockquote className="border-l-4 border-primary pl-4 italic text-muted-foreground my-4">{children}</blockquote>
                                ),
                            }}
                        >
                            {cleanResult(result)}
                        </ReactMarkdown>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
