import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  FileText, 
  Search, 
  Users, 
  CheckCircle, 
  ArrowRight, 
  ArrowLeft,
  Play,
  Target,
  Zap
} from "lucide-react";

interface TutorialFlowProps {
  onComplete: () => void;
}

export default function TutorialFlow({ onComplete }: TutorialFlowProps) {
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
        {
          title: "Welcome to Candidate Matching System",
          subtitle: "Find the perfect candidates for your job openings",
      icon: <Target className="w-12 h-12 text-brand-teal/70" />,
      content: (
        <div className="text-center space-y-4">
          <p className="text-base text-gray-500">
            Our AI-powered system analyzes job descriptions and matches them with the best candidates from our database.
          </p>
          <div className="flex justify-center space-x-3">
            <Badge variant="secondary" className="px-3 py-1 text-xs bg-brand-teal/10 text-brand-teal/80 border-0">
              <Zap className="w-3 h-3 mr-1" />
              AI-Powered Matching
            </Badge>
            <Badge variant="secondary" className="px-3 py-1 text-xs bg-brand-purple/10 text-brand-purple/80 border-0">
              <Users className="w-3 h-3 mr-1" />
              Top Candidates
            </Badge>
          </div>
        </div>
      )
    },
    {
      title: "Step 1: Enter Job Description",
      subtitle: "Describe the role you're looking to fill",
      icon: <FileText className="w-12 h-12 text-brand-purple/70" />,
      content: (
        <div className="space-y-4">
          <div className="bg-gray-50/50 p-3 rounded-lg border border-gray-200">
            <p className="text-xs text-gray-500 mb-2">Example Job Description:</p>
            <p className="text-xs italic text-gray-600">
              "We are looking for a Senior Software Engineer with 5+ years of experience in React, Node.js, and cloud technologies. 
              The ideal candidate should have strong problem-solving skills and experience with microservices architecture..."
            </p>
          </div>
          <p className="text-xs text-gray-500">
            💡 <strong>Tip:</strong> Be specific about requirements, skills, and experience level for better matches.
          </p>
        </div>
      )
    },
    {
      title: "Step 2: AI Analysis",
      subtitle: "Our system analyzes and matches candidates",
      icon: <Search className="w-12 h-12 text-brand-teal/70" />,
      content: (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="w-10 h-10 bg-brand-teal/10 rounded-full flex items-center justify-center mx-auto mb-2">
                <FileText className="w-5 h-5 text-brand-teal/70" />
              </div>
              <p className="text-xs text-gray-500">Parse Job Requirements</p>
            </div>
            <div className="text-center">
              <div className="w-10 h-10 bg-brand-purple/10 rounded-full flex items-center justify-center mx-auto mb-2">
                <Search className="w-5 h-5 text-brand-purple/70" />
              </div>
              <p className="text-xs text-gray-500">Match Skills & Experience</p>
            </div>
            <div className="text-center">
              <div className="w-10 h-10 bg-brand-teal/10 rounded-full flex items-center justify-center mx-auto mb-2">
                <CheckCircle className="w-5 h-5 text-brand-teal/70" />
              </div>
              <p className="text-xs text-gray-500">Rank Candidates</p>
            </div>
          </div>
          <p className="text-xs text-gray-500 text-center">
            Our AI analyzes your job description and finds the best matching candidates from our database.
          </p>
        </div>
      )
    },
    {
      title: "Step 3: Review Results",
      subtitle: "Browse and select the best candidates",
      icon: <Users className="w-12 h-12 text-brand-purple/70" />,
      content: (
        <div className="space-y-4">
          <div className="bg-white/50 border border-gray-200 rounded-lg p-3 shadow-sm">
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand-teal/80 to-brand-purple/80 flex items-center justify-center text-white font-medium text-xs">
                  AR
                </div>
                <div>
                  <h4 className="font-medium text-xs">Ahmed Al-Rasheed</h4>
                  <p className="text-xs text-gray-500">Senior Software Engineer</p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm font-semibold text-brand-teal/80">95%</div>
                <div className="text-xs text-gray-500">Match</div>
              </div>
            </div>
            <div className="flex flex-wrap gap-1 mb-2">
              <Badge variant="secondary" className="text-xs px-2 py-1 bg-brand-teal/10 text-brand-teal/80 border-0">React</Badge>
              <Badge variant="secondary" className="text-xs px-2 py-1 bg-brand-purple/10 text-brand-purple/80 border-0">Node.js</Badge>
              <Badge variant="secondary" className="text-xs px-2 py-1 bg-brand-gray/10 text-brand-gray/80 border-0">AWS</Badge>
            </div>
            <Button size="sm" className="w-full text-xs bg-gradient-to-r from-brand-teal/80 to-brand-purple/80 text-white border-0">
              <FileText className="w-3 h-3 mr-1" />
              View CV
            </Button>
          </div>
          <p className="text-xs text-gray-500 text-center">
            Review candidate profiles, skills, and experience. Click "View CV" to see detailed information.
          </p>
        </div>
      )
    }
  ];

  const nextStep = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const startApplication = () => {
    onComplete();
  };

  return (
    <div className="min-h-screen bg-white flex items-center justify-center p-4">
      <div className="max-w-2xl w-full">
        {/* Progress Indicator */}
        <div className="mb-8">
          <div className="flex justify-center space-x-2 mb-4">
            {steps.map((_, index) => (
              <div
                key={index}
                className={`w-3 h-3 rounded-full transition-all duration-300 ${
                  index <= currentStep 
                    ? 'bg-gradient-to-r from-brand-teal to-brand-purple' 
                    : 'bg-gray-300'
                }`}
              />
            ))}
          </div>
          <div className="text-center">
            <span className="text-sm text-gray-600">
              Step {currentStep + 1} of {steps.length}
            </span>
          </div>
        </div>

        {/* Main Content */}
        <div className="text-center space-y-6">
          {/* Icon */}
          <div className="flex justify-center">
            {steps[currentStep].icon}
          </div>

          {/* Title */}
          <div>
            <h1 className="text-2xl font-medium text-gray-700 mb-2">
              {steps[currentStep].title}
            </h1>
            <p className="text-base text-gray-500">
              {steps[currentStep].subtitle}
            </p>
          </div>

          {/* Content */}
          <div className="max-w-lg mx-auto">
            {steps[currentStep].content}
          </div>

          {/* Navigation */}
          <div className="flex justify-between items-center pt-6">
            <Button
              variant="outline"
              onClick={prevStep}
              disabled={currentStep === 0}
              className="flex items-center"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Previous
            </Button>

            {currentStep === steps.length - 1 ? (
              <Button
                onClick={startApplication}
                className="bg-gradient-to-r from-brand-teal/80 to-brand-purple/80 text-white px-6 py-2 hover:shadow-md hover:shadow-brand-teal/20 transition-all duration-200 hover:scale-102 active:scale-98"
              >
                <Play className="w-4 h-4 mr-2" />
                Start Matching!
              </Button>
            ) : (
              <Button
                onClick={nextStep}
                className="bg-gradient-to-r from-brand-teal/80 to-brand-purple/80 text-white px-5 py-2 hover:shadow-md hover:shadow-brand-teal/20 transition-all duration-200 hover:scale-102 active:scale-98"
              >
                Next
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            )}
          </div>
        </div>

        {/* Skip Option */}
        <div className="text-center mt-4">
          <button
            onClick={startApplication}
            className="text-sm text-gray-400 hover:text-gray-500 transition-colors duration-200"
          >
            Skip Tutorial
          </button>
        </div>
      </div>
    </div>
  );
}
