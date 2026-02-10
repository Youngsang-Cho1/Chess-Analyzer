
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
            className={isAnalyzing ? "analyze-btn-disabled" : "analyze-btn"}
        >
            {isAnalyzing ? `Analyzing ${username}...` : `Analyze ${username}'s Games`}
        </button>
    );
}
