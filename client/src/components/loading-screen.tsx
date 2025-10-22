import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

export default function LoadingScreen() {
  const [progress, setProgress] = useState(0);
  const [statusText, setStatusText] = useState("Initializing analysis...");

  useEffect(() => {
    const steps = [
      { progress: 20, text: "Parsing job requirements...", delay: 800 },
      { progress: 40, text: "Extracting key skills...", delay: 800 },
      { progress: 60, text: "Matching candidate profiles...", delay: 800 },
      { progress: 80, text: "Calculating compatibility scores...", delay: 800 },
      { progress: 100, text: "Finalizing results...", delay: 800 },
    ];

    let currentStep = 0;

    const runStep = () => {
      if (currentStep < steps.length) {
        const step = steps[currentStep];
        setTimeout(() => {
          setProgress(step.progress);
          setStatusText(step.text);
          currentStep++;
          if (currentStep < steps.length) {
            runStep();
          }
        }, step.delay);
      }
    };

    runStep();
  }, []);

  return (
    <section className="bg-card rounded-xl shadow-lg p-12 mb-8 border border-card-border" data-testid="section-loading">
      <div className="text-center">
        {/* Spinner */}
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full mb-6 bg-primary/10">
          <Loader2 className="w-8 h-8 text-primary animate-spin" />
        </div>

        <h3 className="text-xl font-semibold mb-4" data-testid="text-loading-message">
          Analyzing job requirements
        </h3>

        {/* Loading dots */}
        <div className="flex justify-center space-x-1 mb-6">
          <div className="w-2 h-2 rounded-full bg-primary animate-loading-dots" />
          <div 
            className="w-2 h-2 rounded-full bg-primary animate-loading-dots"
            style={{ animationDelay: "0.3s" }}
          />
          <div 
            className="w-2 h-2 rounded-full bg-primary animate-loading-dots"
            style={{ animationDelay: "0.6s" }}
          />
        </div>

        {/* Progress bar */}
        <div className="max-w-md mx-auto">
          <div className="bg-secondary rounded-full h-2 mb-2">
            <div 
              className="h-2 rounded-full transition-all duration-300 bg-gradient-to-r from-brand-teal to-brand-purple"
              style={{ width: `${progress}%` }}
              data-testid="progress-bar"
            />
          </div>
          <p className="text-sm text-muted-foreground" data-testid="text-progress-status">
            {statusText}
          </p>
        </div>
      </div>
    </section>
  );
}
