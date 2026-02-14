
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
import AIInsights from "./components/AIInsights";
import OpeningStats from "./components/OpeningStats";
import OpponentSearch from "./components/OpponentSearch";

interface Stats {
  win_rate: number;
  record: string;
  avg_accuracy: number;
  total_games: number;
  style: string;
  history: any[];
  classifications: Record<string, number>;
  ai_insight: string;
}


export default function Home() {
  const [username, setUsername] = useState("choys1211");
  const [games, setGames] = useState([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [opponent, setOpponent] = useState("");

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

  const runAnalysis = async (limit: number, opponent?: string) => {
    setIsAnalyzing(true);
    try {
      let url = `http://localhost:8000/analyze/${username}?limit=${limit}`;
      if (opponent) {
        url += `&opponent=${opponent}`;
      }

      const options = {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username }),
      };

      // 1. Request Analysis
      await fetch(url, options);

      // 2. Wait for backend batch processing
      // We keep the loading screen up while data is being processed/fetched
      await new Promise((resolve) => setTimeout(resolve, 3000));
      await fetchAllData(username); // First intermediate update

      await new Promise((resolve) => setTimeout(resolve, 5000));
      await fetchAllData(username); // Final update

    } catch (error) {
      console.error("Error during analysis:", error);
      alert("Analysis failed. Please try again.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleAnalyze = (limit: number) => runAnalysis(limit);
  const opponentAnalyze = (limit: number, opponent?: string) => runAnalysis(limit, opponent);

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

        {/* AI Insight */}
        {stats && <AIInsights insight={stats.ai_insight} />}

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
              <MoveQualityChart data={stats.classifications} username={username} />
              <OpeningStats history={stats.history} />
            </div>
          </>
        )}

        {/* Analyze Button */}
        <div className="mb-8 flex flex-col items-end gap-4">
          <AnalyzeButton
            isAnalyzing={isAnalyzing}
            handleAnalyze={handleAnalyze}
            username={username}
          />
          <OpponentSearch
            isAnalyzing={isAnalyzing}
            handleAnalyze={opponentAnalyze}
            username={username}
          />
        </div>


        {/* Game List */}
        <GameList games={games} username={username} />
      </div>
    </div>
  );
}