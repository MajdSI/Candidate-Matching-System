import { useState, useEffect } from "react";

interface IntroAnimationProps {
  onComplete: () => void;
}

export default function IntroAnimation({ onComplete }: IntroAnimationProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [isVisible, setIsVisible] = useState(true);
  const [particles, setParticles] = useState<Array<{id: number, x: number, y: number, size: number, delay: number}>>([]);

  // Generate dynamic particles
  useEffect(() => {
    const newParticles = Array.from({ length: 30 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 3 + 1,
      delay: Math.random() * 2
    }));
    setParticles(newParticles);
  }, []);

  useEffect(() => {
    const steps = [
      { delay: 0, duration: 1200 },      // Logo morph in
      { delay: 1200, duration: 1000 }, // Title typewriter effect
      { delay: 2200, duration: 800 },   // Subtitle reveal
      { delay: 3000, duration: 1200 },  // Advanced loading animation
      { delay: 4200, duration: 800 },   // Morph out transition
    ];

    const timeouts: NodeJS.Timeout[] = [];

    steps.forEach((step, index) => {
      const timeout = setTimeout(() => {
        setCurrentStep(index + 1);
        
        // Complete intro after last step
        if (index === steps.length - 1) {
          setTimeout(() => {
            setIsVisible(false);
            setTimeout(onComplete, 500); // Allow morph out to complete
          }, step.duration);
        }
      }, step.delay);
      
      timeouts.push(timeout);
    });

    return () => {
      timeouts.forEach(clearTimeout);
    };
  }, [onComplete]);

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 z-50 bg-white overflow-hidden">
      {/* Dynamic Particle System */}
      <div className="absolute inset-0">
        {particles.map((particle) => (
          <div
            key={particle.id}
            className="absolute rounded-full bg-gradient-to-r from-brand-teal/20 to-brand-purple/20 animate-pulse"
            style={{
              left: `${particle.x}%`,
              top: `${particle.y}%`,
              width: `${particle.size}px`,
              height: `${particle.size}px`,
              animationDelay: `${particle.delay}s`,
              animationDuration: `${2 + Math.random() * 2}s`
            }}
          />
        ))}
      </div>

      {/* Background Elements */}
      <div className="absolute inset-0 pointer-events-none">
        {/* Floating Circles */}
        <div 
          className={`absolute top-1/4 right-1/4 w-12 h-12 transition-all duration-2000 ${
            currentStep >= 1 ? 'opacity-40 scale-100' : 'opacity-0 scale-0'
          }`}
        >
          <div className="w-full h-full bg-gradient-to-br from-brand-teal/30 to-transparent rounded-full animate-float"></div>
        </div>

        <div 
          className={`absolute top-1/3 left-1/4 w-8 h-8 transition-all duration-2500 ${
            currentStep >= 2 ? 'opacity-30 scale-100' : 'opacity-0 scale-0'
          }`}
        >
          <div className="w-full h-full bg-gradient-to-br from-brand-purple/25 to-transparent rounded-full animate-bounce-slow"></div>
        </div>

        <div 
          className={`absolute bottom-1/3 right-1/3 w-10 h-10 transition-all duration-3000 ${
            currentStep >= 3 ? 'opacity-35 scale-100' : 'opacity-0 scale-0'
          }`}
        >
          <div className="w-full h-full bg-gradient-to-br from-brand-gray/20 to-transparent rounded-full animate-pulse"></div>
        </div>

        {/* Subtle Lines */}
        <div 
          className={`absolute top-1/2 left-0 w-32 h-px transition-all duration-2000 ${
            currentStep >= 2 ? 'opacity-20 translate-x-0' : 'opacity-0 -translate-x-full'
          }`}
        >
          <div className="w-full h-full bg-gradient-to-r from-transparent via-brand-teal/30 to-transparent"></div>
        </div>

        <div 
          className={`absolute bottom-1/4 right-0 w-24 h-px transition-all duration-2500 ${
            currentStep >= 3 ? 'opacity-15 translate-x-0' : 'opacity-0 translate-x-full'
          }`}
        >
          <div className="w-full h-full bg-gradient-to-l from-transparent via-brand-purple/25 to-transparent"></div>
        </div>
      </div>

      {/* Main Content */}
      <div className="relative z-10 min-h-screen flex items-center justify-center">
        <div className="text-center max-w-3xl mx-auto px-4">
          {/* TAHAKOM Logo with Advanced Animation */}
          <div 
            className={`transition-all duration-1200 ${
              currentStep >= 1 
                ? 'opacity-100 scale-100 rotate-0' 
                : 'opacity-0 scale-50 rotate-180'
            }`}
          >
            <div className="relative inline-block">
              <img
                src="/src/tahakom-logo.svg"
                alt="TAHAKOM Logo"
                className="h-32 w-auto mx-auto drop-shadow-2xl hover:scale-110 transition-transform duration-500"
              />
              {/* Subtle Glow Effect */}
              <div className="absolute inset-0 rounded-lg bg-gradient-to-r from-brand-teal/10 to-brand-purple/10 blur-xl -z-10"></div>
            </div>
          </div>

          {/* Title with Typewriter Effect */}
          <div 
            className={`transition-all duration-1000 ${
              currentStep >= 2 
                ? 'opacity-100 translate-y-0' 
                : 'opacity-0 translate-y-8'
            }`}
          >
                <h1 className="text-4xl font-bold bg-gradient-to-r from-brand-teal via-brand-purple to-brand-gray bg-clip-text text-transparent mb-4 animate-gradient-x">
                  Candidate Matching System
                </h1>
          </div>

          {/* Subtitle with Reveal Animation */}
          <div 
            className={`transition-all duration-800 ${
              currentStep >= 3 
                ? 'opacity-100 translate-y-0 scale-100' 
                : 'opacity-0 translate-y-4 scale-95'
            }`}
          >
            <p className="text-xl text-gray-600 mb-8 font-medium">
              <span className="inline-block animate-fade-in-up" style={{ animationDelay: '0.1s' }}>Powered by</span>
              <span className="inline-block mx-2 animate-fade-in-up" style={{ animationDelay: '0.3s' }}>TAHAKOM</span>
              <span className="inline-block animate-fade-in-up" style={{ animationDelay: '0.5s' }}>&</span>
              <span className="inline-block mx-2 animate-fade-in-up" style={{ animationDelay: '0.7s' }}>KAUST Academy</span>
            </p>
          </div>

          {/* Advanced Loading Animation */}
          <div 
            className={`transition-all duration-1200 ${
              currentStep >= 4 
                ? 'opacity-100 scale-100' 
                : 'opacity-0 scale-75'
            }`}
          >
            <div className="flex flex-col items-center">
              <p className="text-gray-500 text-base font-medium animate-pulse">
                Initializing System...
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Background Wave Animation */}
      <div className="absolute bottom-0 left-0 w-full h-32 overflow-hidden">
        <div className="absolute bottom-0 w-full h-full bg-gradient-to-t from-brand-teal/10 via-transparent to-transparent animate-wave"></div>
        <div className="absolute bottom-0 w-full h-full bg-gradient-to-t from-brand-purple/10 via-transparent to-transparent animate-wave-delayed"></div>
      </div>
    </div>
  );
}
