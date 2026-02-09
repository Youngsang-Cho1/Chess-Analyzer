
interface Game {
    white_username: string;
    black_username: string;
    white_result: string;
    black_result: string;
    time_control: string;
    url: string;
}

interface Props {
    games: Game[];
    username: string;
}

export default function GameList({ games, username }: Props) {
    if (games.length === 0) {
        return <div className="text-center text-gray-500 py-10">No games found.</div>;
    }

    return (
        <div className="game-grid">
            {games.map((game, index) => {
                const isWhite = game.white_username.toLowerCase() === username.toLowerCase();
                return (
                    <div key={index} className="game-card group">
                        <h2 className="game-title">
                            {game.white_username} vs {game.black_username}
                        </h2>
                        <p className="game-info">
                            {game.time_control} • {isWhite ? game.white_result : game.black_result}
                        </p>
                        <a href={game.url} target="_blank" rel="noopener noreferrer" className="game-link">
                            View on Chess.com
                        </a>
                    </div>
                );
            })}
        </div>
    );
}
