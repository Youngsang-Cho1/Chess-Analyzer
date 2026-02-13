
interface Props {
    isAnalyzing: boolean;
    handleAnalyze: (limit: number) => void;
    username: string;
}

export default function AnalyzeButton({ isAnalyzing, handleAnalyze, username }: Props) {
    return (
        <div className="analyze-row">
            <input
                id="game-limit"
                type="number"
                min="1"
                max="50"
                placeholder="Games to analyze (default: 5)"
                className="game-limit-input"
                defaultValue={5}
                disabled={isAnalyzing}
            />
            <button
                onClick={() => {
                    const input = document.getElementById("game-limit") as HTMLInputElement;
                    const limit = Number(input.value) || 5; // Default to 5 if empty
                    handleAnalyze(limit);
                }}
                disabled={isAnalyzing}
                className={isAnalyzing ? "analyze-btn-disabled" : "analyze-btn"}
            >
                {isAnalyzing ? `Analyzing ${username}...` : `Analyze ${username}'s Games`}
            </button>
        </div>
    );
}
