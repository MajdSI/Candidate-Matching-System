import { useState, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import LoadingScreen from "@/components/loading-screen";
import ResultsScreen from "@/components/results-screen";
import IntroAnimation from "@/components/intro-animation";
import TutorialFlow from "@/components/tutorial-flow";
import { Sparkles, AlertCircle } from "lucide-react";
import { transformMatchResToCandidate } from "@/lib/utils";
import type { Candidate, MatchReq, MatchRes, ExplainReq } from "@shared/schema";

export default function Home() {
  const [jobDescription, setJobDescription] = useState("");
  const [currentScreen, setCurrentScreen] = useState<"intro" | "tutorial" | "input" | "loading" | "results">("intro");
  const [error, setError] = useState("");
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loadingStartTime, setLoadingStartTime] = useState<number>(0);
  const [explanationLoading, setExplanationLoading] = useState<Set<string>>(new Set()); // Track which candidates are loading explanations

  const analyzeMutation = useMutation({
    mutationFn: async (description: string) => {
      // Prepare request body - use async_explain for better UX
      const requestBody: MatchReq = {
        jd_text: description,
        jd_col: "clean_jd",
        cv_col: "cv_summary",
        resolve_jd_to_col: "jd_summary",
        topk: 5,
        candidate_topk:200,
        rrf_k: 60,
        threshold: null,
        cosine_floor: 0.0,
        alpha: 0.5,
        batch_size: 32,
        async_explain: false  // Return results immediately, fetch explanations separately
      };

      // Call Python backend API directly
      const response = await fetch("http://localhost:8001/match", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Backend API error: ${response.status} - ${errorText}`);
      }

      const matchResults: MatchRes[] = await response.json();
      
      // Debug: Print the full received response
      console.log("=== BACKEND API RESPONSE (DEBUG) ===");
      console.log("Full Response:", JSON.stringify(matchResults, null, 2));
      console.log("Number of results:", matchResults.length);
      console.log("Ranks received:", matchResults.map(m => ({ rank: m.rank, cv_uid: m.cv_uid, final_score: m.final_score })));
      console.log("Sample result (first):", matchResults[0] ? JSON.stringify(matchResults[0], null, 2) : "No results");
      console.log("=== END DEBUG ===");
      
      // Verify we got exactly 5 candidates in rank order
      if (matchResults.length !== 5) {
        console.warn(`WARNING: Expected 5 candidates, got ${matchResults.length}`);
      }
      const ranks = matchResults.map(m => m.rank).sort((a, b) => a - b);
      if (ranks.toString() !== "1,2,3,4,5") {
        console.warn(`WARNING: Ranks are not 1,2,3,4,5. Got: ${ranks}`);
      }
      
      // Transform backend response to Candidate format
      const candidates = matchResults.map(transformMatchResToCandidate);
      
      // Debug: Print transformed candidates
      console.log("=== TRANSFORMED CANDIDATES (DEBUG) ===");
      console.log("Transformed candidates:", JSON.stringify(candidates, null, 2));
      console.log("=== END DEBUG ===");
      
      return { candidates, jd_text: description, matchResults };
    },
    onSuccess: async (data) => {
      setCandidates(data.candidates);
      
      // Show loading screen for at least 1 second for better UX
      const elapsed = Date.now() - loadingStartTime;
      const minLoadingTime = 1000;
      const remainingTime = Math.max(0, minLoadingTime - elapsed);
      
      setTimeout(() => {
        setCurrentScreen("results");
        
        // Fetch explanations asynchronously after showing results
        fetchExplanations(data.jd_text, data.matchResults, data.candidates);
      }, remainingTime);
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : "Failed to analyze job description");
      setCurrentScreen("input");
    },
  });

  // Function to fetch explanations asynchronously
  const fetchExplanations = async (
    jdText: string,
    matchResults: MatchRes[],
    currentCandidates: Candidate[]
  ) => {
    console.log("=== FETCHING EXPLANATIONS ===");
    console.log("Starting explanation fetch for", currentCandidates.length, "candidates");
    
    // Mark all candidates as loading explanations
    setExplanationLoading(new Set(currentCandidates.map(c => c.id)));
    
    try {
      // Prepare explain request - IMPORTANT: Use matchResults in the SAME ORDER as received
      // matchResults are already sorted by rank (1, 2, 3, 4, 5) from the /match endpoint
      console.log("=== PREPARING EXPLAIN REQUEST ===");
      console.log("Candidates being sent for explanation:", matchResults.map(mr => ({
        rank: mr.rank,
        cv_uid: mr.cv_uid,
        final_score: mr.final_score
      })));
      
      const explainReq: ExplainReq = {
        jd_text: jdText,
        candidates: matchResults.map(mr => ({
          cv_uid: mr.cv_uid,
          cv_text: mr.cv_text || "",
          rank: mr.rank,  // CRITICAL: Preserve rank to verify order
          final_score: mr.final_score,
          ce_score: mr.ce_score,
          hybrid_score_0_100: mr.hybrid_score_0_100,
          cv_id: mr.cv_id,
        })),
        max_reasons: 4,
        per_cv_char_budget: 4000,
      };

      const response = await fetch("http://localhost:8001/explain", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(explainReq),
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch explanations: ${response.status}`);
      }

      const explainedResults: MatchRes[] = await response.json();
      
      console.log("=== EXPLANATIONS RECEIVED ===");
      console.log("Explanations:", JSON.stringify(explainedResults, null, 2));
      
      // Update candidates with explanations
      setCandidates(prevCandidates => {
        return prevCandidates.map(candidate => {
          const explained = explainedResults.find(
            er => er.cv_uid.toString() === candidate.id
          );
          if (explained?.explanation) {
            return {
              ...candidate,
              explanation: explained.explanation,
            } as Candidate & { explanation?: MatchRes['explanation'] };
          }
          return candidate;
        });
      });
      
      // Clear loading state
      setExplanationLoading(new Set());
    } catch (error) {
      console.error("Failed to fetch explanations:", error);
      // Clear loading state even on error
      setExplanationLoading(new Set());
      // Optionally show error message to user
    }
  };

  const handleAnalyze = () => {
    console.log("=== ANALYZE BUTTON CLICKED ===");
    console.log("Job Description Length:", jobDescription.length);
    
    setError("");
    
    if (!jobDescription.trim()) {
      setError("Please enter a job description to analyze.");
      return;
    }

    if (jobDescription.trim().length < 10) {
      setError("Job description must be at least 10 characters.");
      return;
    }

    console.log("Starting analysis...");
    setLoadingStartTime(Date.now());
    setCurrentScreen("loading");
    analyzeMutation.mutate(jobDescription);
  };

  const handleNewSearch = () => {
    setJobDescription("");
    setCurrentScreen("input");
    setError("");
    setCandidates([]);
  };

  const handleIntroComplete = () => {
    setCurrentScreen("tutorial");
  };

  const handleTutorialComplete = () => {
    setCurrentScreen("input");
  };

  return (
    <>
      {/* Intro Animation */}
      {currentScreen === "intro" && (
        <IntroAnimation onComplete={handleIntroComplete} />
      )}

      {/* Tutorial Flow */}
      {currentScreen === "tutorial" && (
        <TutorialFlow onComplete={handleTutorialComplete} />
      )}

      {/* Main Application */}
      {currentScreen !== "intro" && currentScreen !== "tutorial" && (
        <div
          className="min-h-screen p-4 bg-white relative overflow-hidden"
        >
          {/* Dynamic Background Elements */}
          <div className="fixed inset-0 pointer-events-none z-0">
            {/* Static Gradient Circles - No Animation */}
            <div className="absolute top-20 left-10 w-64 h-64 bg-brand-teal/15 rounded-full blur-3xl"></div>
            <div className="absolute top-40 right-20 w-48 h-48 bg-brand-purple/15 rounded-full blur-3xl"></div>
            <div className="absolute bottom-40 left-1/4 w-56 h-56 bg-brand-gray/10 rounded-full blur-3xl"></div>
            
            {/* Additional visible accent circles - No Animation */}
            <div className="absolute top-1/2 right-1/3 w-72 h-72 bg-brand-teal/8 rounded-full blur-3xl"></div>
            <div className="absolute bottom-1/4 right-1/4 w-60 h-60 bg-brand-purple/8 rounded-full blur-3xl"></div>
            
            {/* Subtle Grid Pattern */}
            <div className="absolute inset-0 bg-[linear-gradient(90deg,_rgba(174,174,174,0.03)_1px,_transparent_1px),linear-gradient(rgba(174,174,174,0.03)_1px,_transparent_1px)] bg-[size:40px_40px]"></div>
            
            {/* Floating Particles - Subtle Movement */}
            <div className="absolute top-1/4 right-1/4 w-2 h-2 bg-brand-teal/30 rounded-full animate-float" style={{ animationDuration: '8s', animationDelay: '0s' }}></div>
            <div className="absolute top-1/3 left-1/3 w-2 h-2 bg-brand-purple/30 rounded-full animate-float" style={{ animationDuration: '10s', animationDelay: '2s' }}></div>
            <div className="absolute bottom-1/3 right-1/3 w-2 h-2 bg-brand-gray/30 rounded-full animate-float" style={{ animationDuration: '12s', animationDelay: '4s' }}></div>
            <div className="absolute bottom-1/4 left-1/4 w-2 h-2 bg-brand-teal/30 rounded-full animate-float" style={{ animationDuration: '9s', animationDelay: '1s' }}></div>
          </div>
      
      <div className="min-h-screen flex flex-col relative z-10">
        {/* Header - Always visible */}
        <header className="mb-6">
          {/* Logo Section - Top Corners */}
          <div className="flex justify-between items-start mb-6">
            {/* TAHAKOM Logo - Top Left */}
            <div className="flex items-center">
              <img 
                src="/src/tahakom-logo.svg" 
                alt="TAHAKOM Logo" 
                className="h-12 w-auto object-contain hover:scale-105 transition-transform duration-300"
              />
            </div>
            
            {/* KAUST Academy Logo - Top Right */}
            <div className="flex items-center">
              <img 
                src="/src/KAUST_Academy_logo_Full_Color.webp" 
                alt="KAUST Academy Logo" 
                className="h-12 w-auto object-contain hover:scale-105 transition-transform duration-300"
              />
            </div>
          </div>
          
              {/* Title Section - Centered */}
              <div className="text-center">
                    <h1 className="text-3xl font-bold text-gray-800 mb-1" data-testid="text-main-title">
                      Candidate Matching System
                    </h1>
                <p className="text-base text-gray-600" data-testid="text-subtitle">
                  Find the perfect candidates for your job openings
                </p>
              </div>
        </header>

                <main className="max-w-6xl mx-auto w-full flex-1">
                  {/* Input Section */}
                  {currentScreen === "input" && (
                    <section className="bg-white rounded-xl shadow-lg p-6 mb-6 border-2 border-brand-teal/30">
                      <div className="max-w-2xl mx-auto">
                        <Label
                          htmlFor="job-description"
                          className="block text-base font-semibold mb-3"
                        >
                          Job Description
                        </Label>

                        <Textarea
                          id="job-description"
                          data-testid="input-job-description"
                          placeholder="Paste your job description here... Include required skills, experience level, responsibilities, and any specific requirements."
                          className="w-full h-40 p-4 rounded-lg resize-none"
                          value={jobDescription}
                          onChange={(e) => setJobDescription(e.target.value)}
                        />

                        {error && (
                          <div
                            className="mt-4 p-3 bg-destructive/10 border border-destructive/30 text-destructive rounded-lg text-sm flex items-start gap-2"
                            data-testid="text-error-message"
                          >
                            <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                            <span>{error}</span>
                          </div>
                        )}

                        <Button
                          data-testid="button-analyze"
                          onClick={handleAnalyze}
                          disabled={analyzeMutation.isPending}
                          size="lg"
                          className="w-full mt-4 font-semibold bg-gradient-to-r from-brand-teal to-brand-purple hover:shadow-xl hover:shadow-brand-teal/25 hover-elevate active-elevate-2 text-primary-foreground border-0 transition-all duration-200 hover:scale-105 active:scale-95"
                        >
                          <Sparkles className="mr-2 h-5 w-5" />
                          {analyzeMutation.isPending ? "Analyzing..." : "Analyze & Find Matches"}
                        </Button>
                      </div>
                    </section>
                  )}

                  {/* Loading Section */}
                  {currentScreen === "loading" && <LoadingScreen />}

                  {/* Results Section */}
                  {currentScreen === "results" && (
                    <ResultsScreen
                      candidates={candidates}
                      onNewSearch={handleNewSearch}
                    />
                  )}
                </main>

                {/* Footer */}
                <footer className="mt-12 py-4 border-t border-gray-200">
                  <div className="max-w-6xl mx-auto px-4">
                    <div className="flex flex-wrap items-center justify-center gap-3 text-xs text-gray-500">
                      <span>Developed by</span>
                      <div className="flex items-center gap-1">
                        <span className="text-gray-700 font-medium">Majd Alsayari</span>
                        <a 
                          href="https://linkedin.com/in/majd-alsayari" 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
                          title="Majd Alsayari LinkedIn"
                        >
                          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.338 16.338H13.67V12.16c0-.995-.017-2.277-1.387-2.277-1.39 0-1.601 1.086-1.601 2.207v4.248H8.014v-8.59h2.559v1.174h.037c.356-.675 1.227-1.387 2.526-1.387 2.703 0 3.203 1.778 3.203 4.092v4.711zM5.005 6.575a1.548 1.548 0 11-.003-3.096 1.548 1.548 0 01.003 3.096zm-1.337 9.763H6.34v-8.59H3.667v8.59zM17.668 1H2.328C1.595 1 1 1.581 1 2.298v15.403C1 18.418 1.595 19 2.328 19h15.34c.734 0 1.332-.582 1.332-1.299V2.298C19 1.581 18.402 1 17.668 1z" clipRule="evenodd" />
                          </svg>
                        </a>
                      </div>
                      <div className="flex items-center gap-1">
                        <span className="text-gray-700 font-medium">Lina ALsayari</span>
                        <a 
                          href="https://linkedin.com/in/lina-alsayari" 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
                          title="Lina ALsayari LinkedIn"
                        >
                          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.338 16.338H13.67V12.16c0-.995-.017-2.277-1.387-2.277-1.39 0-1.601 1.086-1.601 2.207v4.248H8.014v-8.59h2.559v1.174h.037c.356-.675 1.227-1.387 2.526-1.387 2.703 0 3.203 1.778 3.203 4.092v4.711zM5.005 6.575a1.548 1.548 0 11-.003-3.096 1.548 1.548 0 01.003 3.096zm-1.337 9.763H6.34v-8.59H3.667v8.59zM17.668 1H2.328C1.595 1 1 1.581 1 2.298v15.403C1 18.418 1.595 19 2.328 19h15.34c.734 0 1.332-.582 1.332-1.299V2.298C19 1.581 18.402 1 17.668 1z" clipRule="evenodd" />
                          </svg>
                        </a>
                      </div>
                      <div className="flex items-center gap-1">
                        <span className="text-gray-700 font-medium">Lena ALkhodairi</span>
                        <a 
                          href="https://linkedin.com/in/lena-alkhodairi" 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
                          title="Lena ALkhodairi LinkedIn"
                        >
                          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.338 16.338H13.67V12.16c0-.995-.017-2.277-1.387-2.277-1.39 0-1.601 1.086-1.601 2.207v4.248H8.014v-8.59h2.559v1.174h.037c.356-.675 1.227-1.387 2.526-1.387 2.703 0 3.203 1.778 3.203 4.092v4.711zM5.005 6.575a1.548 1.548 0 11-.003-3.096 1.548 1.548 0 01.003 3.096zm-1.337 9.763H6.34v-8.59H3.667v8.59zM17.668 1H2.328C1.595 1 1 1.581 1 2.298v15.403C1 18.418 1.595 19 2.328 19h15.34c.734 0 1.332-.582 1.332-1.299V2.298C19 1.581 18.402 1 17.668 1z" clipRule="evenodd" />
                          </svg>
                        </a>
                      </div>
                      <span className="text-gray-300">•</span>
                      <div className="flex items-center gap-1">
                        <span>Supervised by</span>
                        <span className="text-gray-700 font-medium">Tanveer</span>
                        <a 
                          href="https://linkedin.com/in/tanveer" 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
                          title="Tanveer LinkedIn"
                        >
                          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.338 16.338H13.67V12.16c0-.995-.017-2.277-1.387-2.277-1.39 0-1.601 1.086-1.601 2.207v4.248H8.014v-8.59h2.559v1.174h.037c.356-.675 1.227-1.387 2.526-1.387 2.703 0 3.203 1.778 3.203 4.092v4.711zM5.005 6.575a1.548 1.548 0 11-.003-3.096 1.548 1.548 0 01.003 3.096zm-1.337 9.763H6.34v-8.59H3.667v8.59zM17.668 1H2.328C1.595 1 1 1.581 1 2.298v15.403C1 18.418 1.595 19 2.328 19h15.34c.734 0 1.332-.582 1.332-1.299V2.298C19 1.581 18.402 1 17.668 1z" clipRule="evenodd" />
                          </svg>
                        </a>
                      </div>
                      <span className="text-gray-300">•</span>
                      <span className="text-gray-400">Powered by TAHAKOM & KAUST Academy</span>
                    </div>
                  </div>
                </footer>
      </div>
        </div>
      )}
    </>
  );
}
