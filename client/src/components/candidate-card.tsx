import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { MapPin, Clock, FileText } from "lucide-react";
import type { Candidate } from "@shared/schema";

interface CandidateCardProps {
  candidate: Candidate;
  onViewCV: () => void;
}

export default function CandidateCard({ candidate, onViewCV }: CandidateCardProps) {
  const matchColor = 
    candidate.matchScore >= 90 ? "text-brand-teal" : 
    candidate.matchScore >= 80 ? "text-brand-purple" : 
    "text-muted-foreground";

  return (
    <div 
      className="bg-white border-2 border-gray-100 rounded-xl p-4 shadow-sm transition-all duration-300 hover-elevate hover:shadow-xl hover:border-brand-teal/30 flex flex-col h-full"
      data-testid={`card-candidate-${candidate.id}`}
    >
      {/* Content Area - grows to fill available space */}
      <div className="flex-1 flex flex-col">
        {/* Header with avatar and match score */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center space-x-3">
            <div 
              className="w-12 h-12 rounded-full flex items-center justify-center text-white font-semibold text-lg bg-gradient-to-br from-brand-teal to-brand-purple"
            >
              {candidate.avatar}
            </div>
            <div>
              <h3 className="font-semibold" data-testid={`text-name-${candidate.id}`}>
                {candidate.name}
              </h3>
              <p className="text-sm text-muted-foreground" data-testid={`text-title-${candidate.id}`}>
                {candidate.title}
              </p>
            </div>
          </div>
          <div className="text-right">
            <div 
              className={`text-2xl font-bold ${matchColor}`}
              data-testid={`text-match-${candidate.id}`}
            >
              {candidate.matchScore}%
            </div>
            <div className="text-xs text-muted-foreground">Match</div>
          </div>
        </div>

        {/* Summary */}
        <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
          {candidate.summary}
        </p>

        {/* Location and experience */}
        <div className="mb-3 space-y-1">
          <div className="flex items-center text-sm text-muted-foreground">
            <MapPin className="w-4 h-4 mr-2 flex-shrink-0" />
            <span className="truncate">{candidate.location}</span>
          </div>
          <div className="flex items-center text-sm text-muted-foreground">
            <Clock className="w-4 h-4 mr-2 flex-shrink-0" />
            {candidate.experience} experience
          </div>
        </div>

        {/* Skills */}
        <div className="mb-3">
          <div className="text-xs text-muted-foreground mb-1">Key Skills</div>
          <div className="flex flex-wrap gap-1">
            {candidate.skills.slice(0, 5).map((skill, index) => (
              <Badge
                key={index}
                variant="secondary"
                className="text-xs px-2 py-1 bg-primary/10 text-primary border-0"
                data-testid={`badge-skill-${candidate.id}-${index}`}
              >
                {skill}
              </Badge>
            ))}
          </div>
        </div>
      </div>

      {/* View CV Button - Fixed at bottom */}
      <Button
        data-testid={`button-view-cv-${candidate.id}`}
        onClick={onViewCV}
        className="w-full bg-gradient-to-r from-brand-teal to-brand-purple text-white border-0 hover-elevate active-elevate-2 hover:shadow-lg hover:shadow-brand-teal/25 transition-all duration-200 hover:scale-105 active:scale-95 mt-auto"
      >
        <FileText className="mr-2 h-4 w-4" />
        View CV
      </Button>
    </div>
  );
}
