"use client";

interface AIInsightsProps {
    insight: string;
}

export default function AIInsights({ insight }: AIInsightsProps) {
    return (
        <div className="ai-insights-card">
            <div className="ai-header">
                <div className="ai-icon">GM</div>
                <div>
                    <h2 className="ai-title">AI Coach</h2>
                    <p className="ai-subtitle">Personalized feedback on your recent games</p>
                </div>
            </div>

            <div className="ai-content-box">
                <p className="ai-text">
                    {insight || "Connect your Groq API Key to receive personalized insights."}
                </p>
            </div>
        </div>
    );
}
