
interface Props {
    isVisible: boolean;
    message?: string;
}

export default function LoadingOverlay({ isVisible, message = "Analyzing..." }: Props) {
    if (!isVisible) return null;

    return (
        <div className="fixed inset-0 bg-black/50 z-50 flex flex-col items-center justify-center backdrop-blur-sm">
            <div className="bg-white p-8 rounded-lg shadow-xl flex flex-col items-center animate-bounce-subtle">
                {/* Simple CSS Spinner */}
                <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mb-4"></div>
                <h2 className="text-xl font-bold text-gray-800 mb-2">Analysis in Progress</h2>
                <p className="text-gray-600 text-center max-w-xs">{message}</p>
            </div>
        </div>
    );
}
