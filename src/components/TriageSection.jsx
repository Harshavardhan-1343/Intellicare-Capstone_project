import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, ArrowLeft } from 'lucide-react';

// Standalone Button component (replace with your own button component)
const Button = ({ children, onClick, variant = "default", className = "", ...props }) => {
  const baseStyles = "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none ring-offset-background px-4 py-2";
  const variants = {
    default: "bg-primary text-primary-foreground hover:bg-primary/90",
    ghost: "hover:bg-accent hover:text-accent-foreground",
  };
  
  return (
    <button
      className={`${baseStyles} ${variants[variant]} ${className}`}
      onClick={onClick}
      {...props}
    >
      {children}
    </button>
  );
};

const triageLevels = [
  {
    id: 'emergency',
    title: 'Emergency',
    emoji: '🔴',
    color: 'triage-emergency',
    bgColor: 'bg-red-500',
    gradient: 'linear-gradient(135deg, hsl(0 85% 60% / 0.9), hsl(0 85% 60% / 0.6))',
    description: 'Life-threatening conditions requiring immediate attention',
    examples: ['Cardiac arrest', 'Severe trauma', 'Respiratory failure', 'Stroke symptoms']
  },
  {
    id: 'urgent',
    title: 'Urgent',
    emoji: '🟠',
    color: 'triage-urgent',
    bgColor: 'bg-orange-500',
    gradient: 'linear-gradient(135deg, hsl(25 100% 55% / 0.9), hsl(25 100% 55% / 0.6))',
    description: 'Critical conditions that need prompt medical care',
    examples: ['Chest pain', 'Severe bleeding', 'High fever', 'Difficulty breathing']
  },
  {
    id: 'semi-urgent',
    title: 'Semi-Urgent',
    emoji: '🟡',
    color: 'triage-semi-urgent',
    bgColor: 'bg-yellow-500',
    gradient: 'linear-gradient(135deg, hsl(50 100% 60% / 0.9), hsl(50 100% 60% / 0.6))',
    description: 'Moderate conditions requiring timely assessment',
    examples: ['Fractures', 'Moderate pain', 'Infections', 'Mental health crises']
  },
  {
    id: 'non-urgent',
    title: 'Non-Urgent',
    emoji: '🟢',
    color: 'triage-non-urgent',
    bgColor: 'bg-green-500',
    gradient: 'linear-gradient(135deg, hsl(120 60% 45% / 0.9), hsl(120 60% 45% / 0.6))',
    description: 'Minor conditions that can wait for standard care',
    examples: ['Minor cuts', 'Cold symptoms', 'Routine check-ups', 'Prescription refills']
  },
  {
    id: 'deceased',
    title: 'Deceased',
    emoji: '⚫',
    color: 'triage-deceased',
    bgColor: 'bg-gray-800',
    gradient: 'linear-gradient(135deg, hsl(0 0% 20% / 0.9), hsl(0 0% 20% / 0.6))',
    description: 'No signs of life, no medical intervention possible',
    examples: ['No pulse', 'No breathing', 'No brain activity', 'Rigor mortis present']
  }
];

const TriageSection = () => {
  const [selectedLevel, setSelectedLevel] = useState(null);
  const [currentIndex, setCurrentIndex] = useState(0);

  const handleLevelClick = (level) => {
    const index = triageLevels.findIndex(l => l.id === level.id);
    setCurrentIndex(index);
    setSelectedLevel(level);
  };

  const handlePrevious = () => {
    const newIndex = currentIndex > 0 ? currentIndex - 1 : triageLevels.length - 1;
    setCurrentIndex(newIndex);
    setSelectedLevel(triageLevels[newIndex]);
  };

  const handleNext = () => {
    const newIndex = currentIndex < triageLevels.length - 1 ? currentIndex + 1 : 0;
    setCurrentIndex(newIndex);
    setSelectedLevel(triageLevels[newIndex]);
  };

  const handleBack = () => {
    setSelectedLevel(null);
  };

  if (selectedLevel) {
    return (
      <div 
        className="min-h-screen transition-all duration-1000 flex items-center justify-center p-8"
        style={{
          background: selectedLevel.gradient
        }}
      >
        <div className="max-w-4xl w-full">
          {/* Navigation */}
          <div className="flex justify-between items-center mb-8">
            <Button
              onClick={handleBack}
              variant="ghost"
              className="text-white hover:bg-white/20 transition-colors"
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              Back to Overview
            </Button>
            
            <div className="flex items-center gap-4">
              <Button
                onClick={handlePrevious}
                variant="ghost"
                className="text-white hover:bg-white/20 transition-colors"
              >
                <ChevronLeft className="w-5 h-5" />
              </Button>
              <span className="text-white font-medium">
                {currentIndex + 1} / {triageLevels.length}
              </span>
              <Button
                onClick={handleNext}
                variant="ghost"
                className="text-white hover:bg-white/20 transition-colors"
              >
                <ChevronRight className="w-5 h-5" />
              </Button>
            </div>
          </div>

          {/* Content */}
          <div className="text-center animate-fade-in-up">
            <div className="text-8xl mb-6">{selectedLevel.emoji}</div>
            <h1 className="text-5xl font-bold text-white mb-4">{selectedLevel.title}</h1>
            <p className="text-xl text-white/90 mb-8 max-w-2xl mx-auto">
              {selectedLevel.description}
            </p>
            
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8 max-w-2xl mx-auto">
              <h3 className="text-2xl font-semibold text-white mb-4">Common Examples</h3>
              <ul className="space-y-3">
                {selectedLevel.examples.map((example, index) => (
                  <li
                    key={index}
                    className="text-white/90 text-lg flex items-center"
                  >
                    <div className="w-2 h-2 bg-white/60 rounded-full mr-3" />
                    {example}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[70vh] bg-gradient-to-br from-slate-50 to-blue-100 flex flex-col items-center p-8">
      {/* Section Title (moved to top) */}
      <h2 className="text-3xl md:text-4xl font-bold text-gray-800 mb-12 text-center">
        Know more about <span className="text-blue-600">Medical Triage</span>
      </h2>
  
      <div className="relative flex items-center justify-center flex-1">
        {/* Central AI Triage Icon */}
        <div className="relative z-10 w-36 h-36 rounded-full bg-gradient-to-br from-blue-600 to-blue-800 shadow-2xl flex items-center justify-center animate-pulse-glow">
          <div className="w-24 h-24 rounded-full bg-white flex items-center justify-center">
            <span className="text-3xl font-bold text-blue-600">AI</span>
          </div>
          <div className="absolute -bottom-5 bg-white rounded-full px-4 py-1 shadow-lg">
            <span className="text-sm font-semibold text-blue-600">AI Triage</span>
          </div>
        </div>
  
        {/* Orbiting Triage Levels */}
        <div className="absolute inset-0">
          {triageLevels.map((level, index) => {
            const angle = index * 72 - 90; // 72 degrees apart, starting from top
            return (
              <div
                key={level.id}
                className="absolute w-24 h-24 animate-orbit cursor-pointer group"
                style={{
                  animationDelay: `${index * -3}s`,
                  left: "50%",
                  top: "50%",
                  marginLeft: "-48px",
                  marginTop: "-48px",
                }}
                onClick={() => handleLevelClick(level)}
              >
                <div
                  className={`w-full h-full rounded-full ${level.bgColor} shadow-lg flex items-center justify-center text-3xl transition-all duration-300 group-hover:scale-110 group-hover:shadow-xl`}
                >
                  {level.emoji}
                </div>
                <div className="absolute -bottom-6 left-1/2 transform -translate-x-1/2 bg-white rounded-lg px-2 py-1 shadow-md opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                  <span className="text-xs font-medium text-gray-800 whitespace-nowrap">
                    {level.title}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
  
      <style jsx>{`
        @keyframes orbit {
          from {
            transform: rotate(0deg) translateX(150px) rotate(0deg);
          }
          to {
            transform: rotate(360deg) translateX(150px) rotate(-360deg);
          }
        }
  
        @keyframes pulse-glow {
          0%,
          100% {
            opacity: 1;
            transform: scale(1);
          }
          50% {
            opacity: 0.8;
            transform: scale(1.05);
          }
        }
  
        @keyframes fade-in-up {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
  
        .animate-orbit {
          animation: orbit 15s linear infinite;
        }
  
        .animate-pulse-glow {
          animation: pulse-glow 2s ease-in-out infinite;
        }
  
        .animate-fade-in-up {
          animation: fade-in-up 0.5s ease-out;
        }
      `}</style>
    </div>
  );
}

export default TriageSection;