import React, { useState, useEffect } from 'react';
import { useProfile } from '../context/ProfileContext';
import { ModelMetrics, ConvergenceData, ModelComparisonRow } from '../types/modelLab';
import { fetchLeaderboard, fetchConvergence, fetchComparison } from '../api/modelLab';
import { Navbar } from '../components/common/Navbar';
import { LeaderboardTable } from '../components/model-lab/LeaderboardTable';
import { ConvergenceChart } from '../components/model-lab/ConvergenceChart';
import { SideBySideCompare } from '../components/model-lab/SideBySideCompare';
import { ExplainabilityCard } from '../components/model-lab/ExplainabilityCard';
import { Cpu, Award, TrendingDown, ArrowLeftRight, BookOpen } from 'lucide-react';

export const ModelLabPage: React.FC = () => {
  const { activeProfile, profiles, selectProfile } = useProfile();
  const [metrics, setMetrics] = useState<ModelMetrics[]>([]);
  const [convergence, setConvergence] = useState<ConvergenceData | null>(null);
  const [comparisonRows, setComparisonRows] = useState<ModelComparisonRow[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState<string>(activeProfile?.id || 'neel');
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let mounted = true;
    async function loadData() {
      setLoading(true);
      try {
        const [m, c, comp] = await Promise.all([
          fetchLeaderboard(),
          fetchConvergence(),
          fetchComparison(selectedProfileId),
        ]);
        if (mounted) {
          setMetrics(m);
          setConvergence(c);
          setComparisonRows(comp);
        }
      } catch (err) {
        console.error('Failed to load Model Lab data:', err);
      } finally {
        if (mounted) setLoading(false);
      }
    }
    loadData();
    return () => {
      mounted = false;
    };
  }, [selectedProfileId]);

  const selectedProfile = profiles.find((p) => p.id === selectedProfileId) || profiles[0];

  return (
    <div className="min-h-screen bg-[#141414] text-white flex flex-col justify-between selection:bg-[#E50914] selection:text-white">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-16 flex-1 w-full space-y-10">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-zinc-800">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="p-1.5 rounded-lg bg-[#E50914]/20 border border-[#E50914]/40 text-[#E50914]">
                <Cpu className="w-5 h-5" />
              </span>
              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
                Model Lab &amp; Evaluation Suite
              </h1>
            </div>
            <p className="text-sm text-zinc-400 max-w-2xl">
              Inspect live offline evaluation benchmarks, SGD training convergence curves, and side-by-side algorithmic comparisons replicating Furtado &amp; Singh (2020).
            </p>
          </div>

          {/* Persona Switcher for Comparison */}
          <div className="flex items-center gap-2 bg-zinc-900 p-1.5 rounded-xl border border-zinc-800 flex-none">
            <span className="text-xs font-semibold text-zinc-400 px-2">
              Inspect Profile:
            </span>
            {profiles.map((p) => (
              <button
                key={p.id}
                onClick={() => {
                  setSelectedProfileId(p.id);
                  selectProfile(p);
                }}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  selectedProfileId === p.id
                    ? 'bg-[#E50914] text-white shadow-md'
                    : 'text-zinc-400 hover:text-white hover:bg-zinc-800'
                }`}
              >
                <img src={p.avatar} alt={p.name} className="w-4 h-4 rounded object-cover" />
                <span>{p.name}</span>
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="py-24 flex flex-col items-center justify-center gap-3">
            <div className="w-10 h-10 border-4 border-[#E50914] border-t-transparent rounded-full animate-spin" />
            <span className="text-xs text-zinc-400 font-medium">
              Loading benchmark metrics &amp; convergence curves...
            </span>
          </div>
        ) : (
          <div className="space-y-10">
            {/* 1. Offline Leaderboard Table */}
            <section className="space-y-3">
              <div className="flex items-center gap-2 text-sm font-bold text-zinc-300 uppercase tracking-wider">
                <Award className="w-4 h-4 text-[#E50914]" />
                <span>1. Offline Metric Leaderboard (MovieLens 1M Test Split)</span>
              </div>
              <LeaderboardTable metrics={metrics} />
            </section>

            {/* 2. Convergence Curves */}
            {convergence && (
              <section className="space-y-3">
                <div className="flex items-center gap-2 text-sm font-bold text-zinc-300 uppercase tracking-wider">
                  <TrendingDown className="w-4 h-4 text-[#E50914]" />
                  <span>2. Biased Matrix Factorization Convergence</span>
                </div>
                <ConvergenceChart data={convergence} />
              </section>
            )}

            {/* 3. Side-by-Side Model Comparison */}
            <section className="space-y-3">
              <div className="flex items-center gap-2 text-sm font-bold text-zinc-300 uppercase tracking-wider">
                <ArrowLeftRight className="w-4 h-4 text-[#E50914]" />
                <span>3. Item-KNN vs Funk-SVD Rank &amp; Score Comparison</span>
              </div>
              <SideBySideCompare
                rows={comparisonRows}
                profileName={selectedProfile?.name || 'Neel'}
              />
            </section>

            {/* 4. Mathematical Explainability Deep-Dive */}
            <section className="space-y-3">
              <div className="flex items-center gap-2 text-sm font-bold text-zinc-300 uppercase tracking-wider">
                <BookOpen className="w-4 h-4 text-[#E50914]" />
                <span>4. Mathematical Explainability Deep Dive</span>
              </div>
              <ExplainabilityCard
                rows={comparisonRows}
                profileId={selectedProfileId}
              />
            </section>
          </div>
        )}
      </main>

      <footer className="border-t border-zinc-800/80 py-8 text-center text-xs text-zinc-500">
        CineMatch Model Lab • Offline Evaluation Harness &amp; Latent Diagnostics
      </footer>
    </div>
  );
};
