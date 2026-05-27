
"use client";
import { useEffect, useState } from "react";
import "./globals.css";
import LoadingOverlay from "./components/LoadingOverlay";
import AnalyzeButton from "./components/AnalyzeButton";
import OpponentSearch from "./components/OpponentSearch";
import LibraryDashboard from "./components/LibraryDashboard";
import PersonalizedInsights from "./components/PersonalizedInsights";

export default function Home() {
  const [username, setUsername] = useState("choys1211");
  const [activeTab, setActiveTab] = useState<"overview" | "insights">("overview");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isFetching, setIsFetching] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => { setMounted(true); }, []);

  const handleSearch = () => {
    if (!username.trim()) return;
    setRefreshKey((k) => k + 1);
  };

  const runAnalysis = async (limit: number, opponent?: string) => {
    setIsAnalyzing(true);
    try {
      let url = `http://localhost:8000/analyze/${username}?limit=${limit}`;
      if (opponent) url += `&opponent=${opponent}`;

      const postRes = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username }),
      });
      if (!postRes.ok) throw new Error(`Analysis request failed: ${postRes.status}`);

      // Poll until count grows
      const initial = await fetch(`http://localhost:8000/games/${username}`).then((r) => r.json());
      const startCount = (initial.games || []).length;
      const target = startCount + limit;
      let errs = 0;

      while (true) {
        await new Promise((res) => setTimeout(res, 5000));
        try {
          const r = await fetch(`http://localhost:8000/games/${username}`);
          if (!r.ok) {
            errs++;
            if (errs >= 5) break;
            continue;
          }
          errs = 0;
          const d = await r.json();
          const n = (d.games || []).length;
          if (n >= target || n > startCount * 1.5) break;
        } catch {
          errs++;
          if (errs >= 5) break;
        }
      }

      setIsFetching(true);
      setRefreshKey((k) => k + 1);
      setIsFetching(false);
    } catch (e) {
      console.error(e);
      alert("Analysis failed.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="analysis-page">
      <LoadingOverlay
        isVisible={isAnalyzing || isFetching}
        message={isAnalyzing ? "Fetching games & running Stockfish..." : "Loading..."}
      />

      <div className="max-w-container">
        <h1 className="page-title">♟ Chess Analyzer</h1>

        <div className="search-container">
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            className="search-input"
            placeholder="Chess.com username"
          />
          <button onClick={handleSearch} className="search-button">Search</button>
        </div>

        <div className="mb-8 flex flex-col items-end gap-4" style={{ marginBottom: "1.5rem" }}>
          <AnalyzeButton
            isAnalyzing={isAnalyzing}
            handleAnalyze={(limit) => runAnalysis(limit)}
            username={username}
          />
          <OpponentSearch
            isAnalyzing={isAnalyzing}
            handleAnalyze={(limit, opp) => runAnalysis(limit, opp)}
            username={username}
          />
        </div>

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

        {mounted && activeTab === "overview" && (
          <LibraryDashboard key={`ov-${refreshKey}`} username={username} />
        )}

        {mounted && activeTab === "insights" && (
          <PersonalizedInsights key={`ins-${refreshKey}`} username={username} />
        )}
      </div>
    </div>
  );
}