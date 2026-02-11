
import Link from "next/link";

interface Game {
    id: number;
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
        return <div className="no-games-msg">No games found.</div>;
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
                        {/* Link = 클릭하면 /game/42 로 이동 (새로고침 없이!) */}
                        <Link href={`/game/${game.id}`} className="game-link">
                            Review Game
                        </Link>
                    </div>
                );
            })}
        </div>
    );
}
