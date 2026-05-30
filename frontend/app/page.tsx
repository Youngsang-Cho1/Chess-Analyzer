
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
import PersonalizedInsights from "./components/PersonalizedInsights";

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
  const [games, setGames] = useState<any[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isFetching, setIsFetching] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState<{ processed: number; requested: number } | null>(null);
  const [mounted, setMounted] = useState(false);
  const [activeTab, setActiveTab] = useState<"overview" | "insights">("overview");

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
      let url = `http://localhost:8000/analyze/${username}?new_games=${limit}`;
      if (opponent) url += `&opponent=${opponent}`;

      const postRes = await fetch(url, { method: "POST" });
      if (!postRes.ok) throw new Error(`Analysis request failed: ${postRes.status}`);

      const { job_id, } = await postRes.json();

      // Poll job status until done or failed
      while (true) {
        await new Promise((resolve) => setTimeout(resolve, 3000));
        const statusRes = await fetch(`http://localhost:8000/analyze/status/${job_id}`);
        if (!statusRes.ok) continue;
        const { status, processed, requested, error } = await statusRes.json();
        setAnalysisProgress({ processed, requested });
        if (status === "failed") throw new Error(error || "Analysis failed");
        if (status === "done") break;
      }
      setAnalysisProgress(null);

      await fetchAllData(username);
    } catch (error) {
      console.error("Error during analysis:", error);
      alert(`Analysis failed: ${error}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleAnalyze = (limit: number) => runAnalysis(limit);
  const opponentAnalyze = (limit: number, opponent?: string) => runAnalysis(limit, opponent);

  return (
    <div className="analysis-page">
      <LoadingOverlay isVisible={isAnalyzing || isFetching} message={isAnalyzing ? "Connecting to Chess.com & Initializing Stockfish..." : "Loading Data..."} progress={analysisProgress} />

      <div className="max-w-container">
        <h1 className="page-title">♞ Chess Analyzer</h1>

        {/* Search + Analyze hero row */}
        <div className="hero-row">
          <div className="hero-search-card">
            <div className="analyze-hero-label">PLAYER</div>
            <div className="analyze-hero-controls">
              <div className="search-container" style={{ marginBottom: 0, flex: 1 }}>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                  className="search-input"
                  placeholder="Chess.com username…"
                />
                <button onClick={handleSearch} className="search-button">Search</button>
              </div>
            </div>
          </div>
          <AnalyzeButton isAnalyzing={isAnalyzing} handleAnalyze={handleAnalyze} username={username} />
          <OpponentSearch isAnalyzing={isAnalyzing} handleAnalyze={opponentAnalyze} username={username} />
        </div>

        {/* Tabs */}
        <div className="tab-bar">
          <button
            onClick={() => setActiveTab("overview")}
            className={`tab-button ${activeTab === "overview" ? "tab-button-active" : ""}`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab("insights")}
            className={`tab-button ${activeTab === "insights" ? "tab-button-active" : ""}`}
          >
            Insights
          </button>
        </div>

        {activeTab === "overview" && (
          <>
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
          </>
        )}

        {activeTab === "insights" && mounted && (
          <PersonalizedInsights username={username} />
        )}

        {/* Game List */}
        <GameList games={games} username={username} />
      </div>
    </div>
  );
}