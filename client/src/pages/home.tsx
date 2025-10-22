import { useState, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import LoadingScreen from "@/components/loading-screen";
import ResultsScreen from "@/components/results-screen";
import { Sparkles, AlertCircle } from "lucide-react";
import { apiRequest } from "@/lib/queryClient";
import type { Candidate } from "@shared/schema";

export default function Home() {
  const [jobDescription, setJobDescription] = useState("");
  const [currentScreen, setCurrentScreen] = useState<"input" | "loading" | "results">("input");
  const [error, setError] = useState("");
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loadingStartTime, setLoadingStartTime] = useState<number>(0);

  const analyzeMutation = useMutation({
    mutationFn: async (description: string) => {
      const response = await apiRequest<{ candidates: Candidate[] }>(
        "POST",
        "/api/analyze",
        { description }
      );
      return response;
    },
    onSuccess: (data) => {
      setCandidates(data.candidates);
      
      // Show loading screen for at least 2 seconds for better UX
      const elapsed = Date.now() - loadingStartTime;
      const minLoadingTime = 2000;
      const remainingTime = Math.max(0, minLoadingTime - elapsed);
      
      setTimeout(() => {
        setCurrentScreen("results");
      }, remainingTime);
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : "Failed to analyze job description");
      setCurrentScreen("input");
    },
  });

  const handleAnalyze = () => {
    setError("");
    
    if (!jobDescription.trim()) {
      setError("Please enter a job description to analyze.");
      return;
    }

    if (jobDescription.trim().length < 10) {
      setError("Job description must be at least 10 characters.");
      return;
    }

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

  return (
    <div 
      className="min-h-screen p-6 bg-gradient-to-br from-brand-gray via-brand-teal to-brand-purple"
    >
      <div className="min-h-screen flex flex-col">
        {/* Header - Always visible */}
        <header className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2" data-testid="text-main-title">
            HR Talent Matching Wizard
          </h1>
          <p className="text-lg text-gray-600" data-testid="text-subtitle">
            Find the perfect candidates for your job openings
          </p>
        </header>

        <main className="max-w-6xl mx-auto w-full flex-1">
          {/* Input Section */}
          {currentScreen === "input" && (
            <section className="bg-card rounded-xl shadow-lg p-8 mb-8 border border-card-border">
              <div className="max-w-2xl mx-auto">
                <Label 
                  htmlFor="job-description" 
                  className="block text-lg font-semibold mb-4"
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
                  className="w-full mt-6 font-semibold bg-gradient-to-r from-brand-teal to-brand-purple hover-elevate active-elevate-2 text-primary-foreground border-0"
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
      </div>
    </div>
  );
}
