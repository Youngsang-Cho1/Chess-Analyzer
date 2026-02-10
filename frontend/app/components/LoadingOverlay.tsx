
interface Props {
    isVisible: boolean;
    message?: string;
}

export default function LoadingOverlay({ isVisible, message = "Analyzing..." }: Props) {
    if (!isVisible) return null;

    return (
        <div className="loading-overlay">
            <div className="loading-box animate-bounce-subtle">
                <div className="loading-spinner"></div>
                <h2 className="loading-title">Analysis in Progress</h2>
                <p className="loading-text">{message}</p>
            </div>
        </div>
    );
}
