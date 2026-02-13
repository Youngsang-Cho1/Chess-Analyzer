interface Props {
    isAnalyzing: boolean;
    handleAnalyze: (limit: number, opponent?: string) => void;
    username: string;
}

export default function OpponentSearch({ isAnalyzing, handleAnalyze, username }: Props) {
    return (
        <div className="analyze-row">
            <input
                id="opponent-input"
                type="text"
                placeholder="Opponent Username"
                className="game-limit-input"
                style={{ width: '180px', textAlign: 'left' }}
                disabled={isAnalyzing}
            />
            <input
                id="opponent-limit"
                type="number"
                min="1"
                max="20"
                placeholder="Games"
                className="game-limit-input"
                defaultValue={5}
                disabled={isAnalyzing}
            />
            <button
                onClick={() => {
                    const limitInput = document.getElementById("opponent-limit") as HTMLInputElement;
                    const opponentInput = document.getElementById("opponent-input") as HTMLInputElement;

                    const limit = limitInput ? parseInt(limitInput.value) || 5 : 5;
                    const opponent = opponentInput ? opponentInput.value.trim() : "";

                    if (!opponent) {
                        alert("Please enter an opponent username.");
                        return;
                    }

                    handleAnalyze(limit, opponent);
                }}
                disabled={isAnalyzing}
                className={isAnalyzing ? "analyze-btn-disabled" : "analyze-btn"} // Use consistent class names
            >
                {isAnalyzing ? "Analyzing..." : `Analyze vs Opponent`}
            </button>
        </div>
    );
}