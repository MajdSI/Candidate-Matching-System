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
      <section className="bg-white rounded-xl shadow-lg p-6 mb-6 border-2 border-gray-100">
        <div className="text-center py-12">
          <div className="w-20 h-20 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
            <AlertCircle className="w-10 h-10 text-gray-400" />
          </div>
          <h3 className="text-xl font-semibold mb-2 text-gray-800">No Candidates Found</h3>
          <p className="text-gray-600 mb-2 max-w-md mx-auto">
            There are currently no candidates in the database matching your job description.
          </p>
          <p className="text-sm text-gray-500 mb-6">
            Try adjusting your search criteria or contact the system administrator to add candidate profiles.
          </p>
          <Button 
            onClick={onNewSearch} 
            variant="default"
            className="bg-gradient-to-r from-brand-teal to-brand-purple text-white border-0 hover:shadow-lg hover:shadow-brand-teal/25 transition-all duration-200 hover:scale-105 active:scale-95"
          >
            <Search className="mr-2 h-4 w-4" />
            Try Different Search
          </Button>
        </div>
      </section>
    );
  }

  return (
    <>
      <section className="animate-slide-up" data-testid="section-results">
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6 border-2 border-gray-100">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
            <h2 className="text-xl font-bold" data-testid="text-results-title">
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

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 items-stretch" data-testid="grid-candidates">
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
