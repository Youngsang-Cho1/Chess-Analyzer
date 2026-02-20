
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
  const [isFetching, setIsFetching] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [opponent, setOpponent] = useState("");

  // Prevent hydration mismatch for charts
  useEffect(() => {
    setMounted(true);
  }, []);

  const fetchAllData = async (user: string) => {
    setIsFetching(true);
    try {
      const resGames = await fetch(`http://localhost:8000/games/${user}`);
      const dataGames = await resGames.json();
      setGames(dataGames.games || []);

      const resStats = await fetch(`http://localhost:8000/stats/${user}`);
      const dataStats = await resStats.json();
      setStats(dataStats.stats || null);

    } catch (err) {
      console.error("Failed to fetch data:", err);
    } finally {
      setIsFetching(false);
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
      const postRes = await fetch(url, options);
      if (!postRes.ok) {
        throw new Error(`Analysis request failed with status: ${postRes.status}`);
      }

      // 2. Poll the backend until the number of games increases by 'limit'
      const initialGamesCount = games.length;
      let targetGamesCount = initialGamesCount + limit;
      let consecutiveErrors = 0;

      while (true) {
        await new Promise((resolve) => setTimeout(resolve, 5000)); // wait 5 seconds

        try {
          const resGames = await fetch(`http://localhost:8000/games/${username}`);

          if (!resGames.ok) {
            consecutiveErrors++;
            if (consecutiveErrors >= 5) {
              throw new Error("Backend repeatedly failed to respond.");
            }
            console.error(`Backend error during polling (Attempt ${consecutiveErrors}/5), retrying...`);
            continue;
          }

          // Success, reset error counter
          consecutiveErrors = 0;

          const dataGames = await resGames.json();
          const currentGamesCount = (dataGames.games || []).length;

          // Break if we hit our target or if a ton of new games got added unexpectedly
          if (currentGamesCount >= targetGamesCount || currentGamesCount > initialGamesCount * 1.5) {
            break;
          }
        } catch (e) {
          consecutiveErrors++;
          if (consecutiveErrors >= 5) {
            console.error("Max consecutive polling errors reached. Aborting analysis wait.");
            break; // Break loop but still try to fetch whatever data exists below
          }
          console.error(`Network error during polling (Attempt ${consecutiveErrors}/5). Waiting...`, e);
        }
      }

      // Finally, fetch all data to update the UI
      await fetchAllData(username);

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
      <LoadingOverlay isVisible={isAnalyzing || isFetching} message={isAnalyzing ? "Connecting to Chess.com & Initializing Stockfish..." : "Loading Data..."} />

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