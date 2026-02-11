"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import ChessBoard from "../../components/ChessBoard";

// Game data from backend
interface GameData {
    id: number;
    pgn: string;
    white_username: string;
    black_username: string;
    white_result: string;
    black_result: string;
    time_control: string;
    opening: string;
}

export default function GamePage() {
    // useParams() = URL에서 [id] 값을 자동으로 꺼내줌
    // /game/42 접속하면 → params.id = "42"
    const params = useParams();
    const [game, setGame] = useState<GameData | null>(null);

    // 페이지 열리면 백엔드에서 게임 데이터 가져옴
    useEffect(() => {
        const fetchGame = async () => {
            const res = await fetch(`http://localhost:8000/game/${params.id}`);
            const data = await res.json();
            setGame(data.game);
        };
        fetchGame();
    }, [params.id]);

    if (!game) {
        return <div className="analysis-page">Loading...</div>;
    }

    return (
        <div className="analysis-page">
            <div className="max-w-container">
                {/* 게임 정보 헤더 */}
                <h1 className="page-title">
                    {game.white_username} vs {game.black_username}
                </h1>
                <p style={{ color: "#64748b", marginBottom: "2rem" }}>
                    {game.opening} • {game.time_control}
                </p>

                {/* 체스보드 */}
                <ChessBoard chess_PGN={game.pgn} />
            </div>
        </div>
    );
}
