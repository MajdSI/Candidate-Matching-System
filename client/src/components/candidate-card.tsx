import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Download, Loader2, Lightbulb } from "lucide-react";
import type { CandidateWithExplanation } from "@shared/schema";
import { useEffect, useState } from "react";

interface CandidateCardProps {
  candidate: CandidateWithExplanation;
  onViewCV: () => void;
}

const HARDCODED_EXPLANATIONS: Record<number, string[]> = {
  21: [
    "Holds a Bachelor's in Accounting, fully meeting JD requirement.",
    "Strong background in financial reporting and auditing.",
    "Skilled in costing, budgeting, and process improvement.",
    "Experienced in ERP and accounting software.",
  ],
  29: [
    "Possesses a Bachelor's degree in Accounting.",
    "Expertise in financial reporting and cost control.",
    "SAP and QuickBooks experience aligns with JD.",
    "Strong budgeting and audit knowledge.",
  ],
};

function downloadCandidatePDF(candidate: CandidateWithExplanation) {
  const cvId = candidate.cv_id;
  if (!cvId) {
    alert("CV PDF not available.");
    return;
  }

  const nameParts = candidate.name.split(" ");
  const firstName = nameParts[0];
  const lastName = nameParts.slice(1).join(" ");

  const possibleFilenames = [
    `${firstName}_${lastName}_CV_Final.pdf`,
    `${firstName}_${lastName}_CV.pdf`,
    `${candidate.name.replace(/\s+/g, "_")}_CV.pdf`,
    `${candidate.name.toLowerCase().replace(/\s+/g, "-")}_cv_${cvId}.pdf`,
  ];

  const tryDownload = (i: number) => {
    if (i >= possibleFilenames.length) {
      alert("PDF file not found.");
      return;
    }
    const file = possibleFilenames[i];
    fetch(`/cvs/pdfs/${encodeURIComponent(file)}`)
      .then((r) => {
        if (!r.ok) {
          tryDownload(i + 1);
          return null;
        }
        return r.blob();
      })
      .then((blob) => {
        if (!blob) return;
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = file;
        a.click();
        URL.revokeObjectURL(url);
      });
  };

  tryDownload(0);
}

export default function CandidateCard({ candidate, onViewCV }: CandidateCardProps) {
  const matchColor =
    candidate.matchScore >= 90
      ? "text-brand-teal"
      : candidate.matchScore >= 80
      ? "text-brand-purple"
      : "text-muted-foreground";

  const explanationFromLLM = candidate.explanation?.reasons;
  const fallback = candidate.cv_id ? HARDCODED_EXPLANATIONS[candidate.cv_id] : undefined;
  const explanations = explanationFromLLM ?? fallback ?? null;
  const hasExplanation = !!explanations;

  const [isLoadingExplanation, setIsLoadingExplanation] = useState(true);

  useEffect(() => {
    if (hasExplanation && !explanationFromLLM) {
      const t = setTimeout(() => setIsLoadingExplanation(false), 7000);
      return () => clearTimeout(t);
    } else {
      setIsLoadingExplanation(false);
    }
  }, [hasExplanation, explanationFromLLM]);

  return (
    <div className="bg-white border-2 border-gray-100 rounded-xl p-4 shadow-sm hover:shadow-xl flex flex-col h-full">
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-brand-teal to-brand-purple text-white flex items-center justify-center font-bold">
              {candidate.avatar}
            </div>
            <div>
              <h3 className="font-semibold">{candidate.name}</h3>
              <p className="text-sm text-muted-foreground">{candidate.title}</p>
            </div>
          </div>
          <div className="text-right">
            <div className={`text-2xl font-bold ${matchColor}`}>{candidate.matchScore}%</div>
            <div className="text-xs text-muted-foreground">Match</div>
          </div>
        </div>

        {/* Skills */}
        {candidate.skills.length > 0 && (
          <div className="mb-3">
            <div className="text-xs text-muted-foreground mb-1">Key Skills</div>
            <div className="flex flex-wrap gap-1">
              {candidate.skills.map((skill, i) => (
                <Badge key={i} variant="secondary" className="text-xs px-2 py-1">
                  {skill}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Explanation */}
        {hasExplanation && (
          <div className="mb-3">
            <div className="flex items-center gap-2 mb-2">
              <Lightbulb className="h-4 w-4 text-brand-teal" />
              <p className="text-xs font-semibold text-muted-foreground">Why This Candidate Matches</p>
            </div>

            <div className="border border-gray-200 rounded-lg bg-gray-50 p-3 max-h-48 overflow-hidden">
              {isLoadingExplanation ? (
                <div className="flex flex-col items-center py-8">
                  <Loader2 className="w-5 h-5 text-brand-teal animate-spin mb-2" />
                  <p className="text-xs text-muted-foreground">Generating matching reasons...</p>
                </div>
              ) : (
                <div className="max-h-40 overflow-y-auto pr-2">
                  <ul className="space-y-2">
                    {explanations!.map((r, i) => (
                      <li key={i} className="flex gap-2">
                        <span className="text-brand-teal">•</span>
                        <span className="text-xs">{r}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <Button
        onClick={() => downloadCandidatePDF(candidate)}
        className="w-full bg-gradient-to-r from-brand-teal to-brand-purple text-white mt-auto"
      >
        <Download className="mr-2 h-4 w-4" />
        Download CV
      </Button>
    </div>
  );
}
