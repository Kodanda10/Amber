/**
 * FE-CORE-001: Sentiment Intensity Visualization
 * Visual indicator showing sentiment score intensity
 */
import React from 'react';

interface SentimentBarProps {
  score: number; // -1 to 1
  label: string;
}

export const SentimentBar: React.FC<SentimentBarProps> = ({ score, label }) => {
  // Normalize score to 0-100 range for width
  const normalizedScore = ((score + 1) / 2) * 100;
  
  // Determine color based on score
  let colorClass = 'bg-gray-400';
  if (score > 0.3) {
    colorClass = 'bg-green-500';
  } else if (score < -0.3) {
    colorClass = 'bg-red-500';
  }
  
  return (
    <div className="sentiment-bar-container" data-testid="sentiment-bar-container">
      <div className="flex items-center gap-2">
        <span className="text-xs text-gray-600 dark:text-gray-400 min-w-[60px]">{label}</span>
        <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            className={`h-full ${colorClass} transition-all duration-300`}
            style={{ width: `${normalizedScore}%` }}
            data-testid="sentiment-bar-fill"
          />
        </div>
        <span className="text-xs text-gray-500 dark:text-gray-400 min-w-[40px] text-right" data-testid="sentiment-score">
          {score.toFixed(2)}
        </span>
      </div>
    </div>
  );
};
