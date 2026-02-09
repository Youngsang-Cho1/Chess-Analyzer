
interface Props {
    isAnalyzing: boolean;
    handleAnalyze: () => void;
    username: string;
}

export default function AnalyzeButton({ isAnalyzing, handleAnalyze, username }: Props) {
    return (
        <button
            onClick={handleAnalyze}
            disabled={isAnalyzing}
            className={`px-4 py-2 rounded font-bold text-white transition-all 
        ${isAnalyzing ? "bg-gray-400 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-700 shadow-md"}`}
        >
            {isAnalyzing ? `Analyzing ${username}...` : `Analyze ${username}'s Games 🔄`}
        </button>
    );
}
