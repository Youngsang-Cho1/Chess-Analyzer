
"use client";
import { useEffect, useState } from "react";
import "./globals.css";
import StatsDashboard from "./components/StatsDashboard";
import GameList from "./components/GameList";
import AnalyzeButton from "./components/AnalyzeButton";
import LoadingOverlay from "./components/LoadingOverlay";
import AccuracyChart from "./components/AccuracyChart";
import ResultDistributionChart from "./components/ResultDistributionChart";
import MoveQualityChart from "./components/MoveQualityChart";
import OpeningStats from "./components/OpeningStats";

interface Stats {
  win_rate: number;
  record: string;
  avg_accuracy: number;
  total_games: number;
  style: string;
  history: any[];
  classifications: Record<string, number>;
}

export default function Home() {
  const [username, setUsername] = useState("choys1211");
  const [games, setGames] = useState([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [mounted, setMounted] = useState(false);

  // Prevent hydration mismatch for charts
  useEffect(() => {
    setMounted(true);
  }, []);

  const fetchAllData = async (user: string) => {
    try {
      const resGames = await fetch(`http://localhost:8000/games/${user}`);
      const dataGames = await resGames.json();
      setGames(dataGames.games || []);

      const resStats = await fetch(`http://localhost:8000/stats/${user}`);
      const dataStats = await resStats.json();
      setStats(dataStats.stats || null);

    } catch (err) {
      console.error("Failed to fetch data:", err);
    }
  };

  useEffect(() => {
    fetchAllData(username);
  }, []);

  const handleSearch = () => {
    if (!username.trim()) return;
    fetchAllData(username);
  };

  const handleAnalyze = async () => {
    setIsAnalyzing(true);
    try {
      const url = `http://localhost:8000/analyze/${username}`;
      const options = {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username }),
      };
      await fetch(url, options);

      // Artificial delay
      await new Promise((resolve) => setTimeout(resolve, 3000));

      alert(`Optimization started for ${username}. Data will refresh automatically.`);

      fetchAllData(username);

      setTimeout(() => {
        fetchAllData(username);
      }, 10000);

    } catch (error) {
      console.error("Error:", error);
      alert("Analysis failed.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="analysis-page">
      <LoadingOverlay isVisible={isAnalyzing} message="Connecting to Chess.com & Initializing Stockfish..." />

      <div className="max-w-container">
        <h1 className="page-title">♟️ Chess Analyzer</h1>

        {/* Search Bar */}
        <div className="search-container">
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            className="search-input"
            placeholder="Enter Chess.com Username..."
          />
          <button
            onClick={handleSearch}
            className="search-button"
          >
            Search
          </button>
        </div>

        {/* Stats Dashboard */}
        <StatsDashboard stats={stats} />

        {/* Charts Section */}
        {mounted && stats && stats.history && stats.history.length > 0 && (
          <>
            {/* Row 1: Trends */}
            <div className="chart-grid">
              <AccuracyChart history={stats.history} />
              <ResultDistributionChart history={stats.history} />
            </div>

            {/* Row 2: Deep Analysis */}
            <div className="chart-grid">
              <MoveQualityChart data={stats.classifications} />
              <OpeningStats history={stats.history} />
            </div>
          </>
        )}

        {/* Analyze Button */}
        <div className="mb-8 flex justify-end">
          <AnalyzeButton
            isAnalyzing={isAnalyzing}
            handleAnalyze={handleAnalyze}
            username={username}
          />
        </div>

        {/* Game List */}
        <GameList games={games} username={username} />
      </div>
    </div>
  );
}