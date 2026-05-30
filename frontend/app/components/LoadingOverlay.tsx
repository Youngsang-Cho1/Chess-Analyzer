
interface Props {
    isVisible: boolean;
    message?: string;
    progress?: { processed: number; requested: number } | null;
}

export default function LoadingOverlay({ isVisible, message = "Analyzing...", progress }: Props) {
    if (!isVisible) return null;

    const pct = progress && progress.requested > 0
        ? Math.round((progress.processed / progress.requested) * 100)
        : null;

    return (
        <div className="loading-overlay">
            <div className="loading-box animate-bounce-subtle">
                <div className="loading-spinner"></div>
                <h2 className="loading-title">Analysis in Progress</h2>
                <p className="loading-text">{message}</p>
                {pct !== null && (
                    <div className="w-full mt-3">
                        <div className="flex justify-between text-xs text-gray-400 mb-1">
                            <span>{progress!.processed} / {progress!.requested} games</span>
                            <span>{pct}%</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2">
                            <div
                                className="bg-green-500 h-2 rounded-full transition-all duration-500"
                                style={{ width: `${pct}%` }}
                            />
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
