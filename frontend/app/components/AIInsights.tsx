"use client";

interface AIInsightsProps {
    insight: string;
}

export default function AIInsights({ insight }: AIInsightsProps) {
    return (
        <div className="ai-insights-card">
            <div className="ai-header">
                <div className="ai-icon">
                    <span className="text-2xl"></span>
                </div>
                <div>
                    <h2 className="ai-title">AI Coach's Analysis</h2>
                    <p className="ai-subtitle">Personalized feedback based on your recent games</p>
                </div>
            </div>

            <div className="ai-content-box">
                <p className="ai-text">
                    {insight || "Connect your Groq API Key to receive personalized coaching insights."}
                </p>
            </div>
        </div>
    );
}
