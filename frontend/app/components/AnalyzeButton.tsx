
interface Props {
    isAnalyzing: boolean;
    handleAnalyze: (limit: number) => void;
    username: string;
}

export default function AnalyzeButton({ isAnalyzing, handleAnalyze, username }: Props) {
    return (
        <div className="analyze-row">
            <select
                id="game-limit"
                defaultValue={5}
                className="game-limit-select"
                disabled={isAnalyzing}
            >
                <option value={5}>5 games</option>
                <option value={10}>10 games</option>
                <option value={20}>20 games</option>
                <option value={50}>50 games</option>
            </select>
            <button
                onClick={() => {
                    const select = document.getElementById("game-limit") as HTMLSelectElement;
                    handleAnalyze(Number(select.value));
                }}
                disabled={isAnalyzing}
                className={isAnalyzing ? "analyze-btn-disabled" : "analyze-btn"}
            >
                {isAnalyzing ? `Analyzing ${username}...` : `Analyze ${username}'s Games`}
            </button>
        </div>
    );
}
