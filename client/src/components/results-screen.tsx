import { useState } from "react";
import { Button } from "@/components/ui/button";
import CandidateCard from "@/components/candidate-card";
import CVDialog from "@/components/cv-dialog";
import { Search, AlertCircle } from "lucide-react";
import type { Candidate } from "@shared/schema";

interface ResultsScreenProps {
  candidates: Candidate[];
  onNewSearch: () => void;
}

export default function ResultsScreen({ candidates, onNewSearch }: ResultsScreenProps) {
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);

  if (!candidates || candidates.length === 0) {
    return (
      <section className="bg-card rounded-xl shadow-lg p-12 mb-8 border border-card-border">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
          <h3 className="text-xl font-semibold mb-2">No Candidates Found</h3>
          <p className="text-muted-foreground mb-6">
            No matching candidates were found for this job description.
          </p>
          <Button 
            onClick={onNewSearch} 
            variant="secondary" 
            className="hover-elevate active-elevate-2"
          >
            New Search
          </Button>
        </div>
      </section>
    );
  }

  return (
    <>
      <section className="animate-slide-up" data-testid="section-results">
        <div className="bg-card rounded-xl shadow-lg p-8 mb-8 border border-card-border">
          <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
            <h2 className="text-2xl font-bold" data-testid="text-results-title">
              Top Matching Candidates
            </h2>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-muted-foreground">
                Sorted by match score
              </span>
              <Button
                data-testid="button-new-search"
                onClick={onNewSearch}
                variant="secondary"
                className="hover-elevate active-elevate-2"
              >
                <Search className="mr-2 h-4 w-4" />
                New Search
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="grid-candidates">
            {candidates.map((candidate) => (
              <CandidateCard
                key={candidate.id}
                candidate={candidate}
                onViewCV={() => setSelectedCandidate(candidate)}
              />
            ))}
          </div>
        </div>
      </section>

      {/* CV Dialog */}
      <CVDialog
        candidate={selectedCandidate}
        open={!!selectedCandidate}
        onOpenChange={(open) => !open && setSelectedCandidate(null)}
      />
    </>
  );
}
