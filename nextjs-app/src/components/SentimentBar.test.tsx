/**
 * FE-CORE-001: Post Sentiment Visualization Tests
 * Tests for sentiment intensity visualization component
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';

// Sentiment intensity component
interface SentimentBarProps {
  score: number; // -1 to 1
  label: string;
}

const SentimentBar: React.FC<SentimentBarProps> = ({ score, label }) => {
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

describe('FE-CORE-001: Sentiment Visualization', () => {
  it('renders sentiment bar with score', () => {
    render(<SentimentBar score={0.75} label="Positive" />);
    
    expect(screen.getByTestId('sentiment-bar-container')).toBeInTheDocument();
    expect(screen.getByTestId('sentiment-bar-fill')).toBeInTheDocument();
    expect(screen.getByTestId('sentiment-score')).toHaveTextContent('0.75');
    expect(screen.getByText('Positive')).toBeInTheDocument();
  });

  it('shows green color for positive sentiment (>0.3)', () => {
    render(<SentimentBar score={0.75} label="Positive" />);
    
    const fill = screen.getByTestId('sentiment-bar-fill');
    expect(fill.className).toContain('bg-green-500');
  });

  it('shows red color for negative sentiment (<-0.3)', () => {
    render(<SentimentBar score={-0.75} label="Negative" />);
    
    const fill = screen.getByTestId('sentiment-bar-fill');
    expect(fill.className).toContain('bg-red-500');
  });

  it('shows gray color for neutral sentiment (-0.3 to 0.3)', () => {
    render(<SentimentBar score={0.1} label="Neutral" />);
    
    const fill = screen.getByTestId('sentiment-bar-fill');
    expect(fill.className).toContain('bg-gray-400');
  });

  it('calculates correct width for positive score', () => {
    render(<SentimentBar score={0.5} label="Positive" />);
    
    const fill = screen.getByTestId('sentiment-bar-fill');
    // score 0.5 -> normalized to 75% width
    expect(fill.style.width).toBe('75%');
  });

  it('calculates correct width for negative score', () => {
    render(<SentimentBar score={-0.5} label="Negative" />);
    
    const fill = screen.getByTestId('sentiment-bar-fill');
    // score -0.5 -> normalized to 25% width
    expect(fill.style.width).toBe('25%');
  });

  it('calculates correct width for neutral score', () => {
    render(<SentimentBar score={0} label="Neutral" />);
    
    const fill = screen.getByTestId('sentiment-bar-fill');
    // score 0 -> normalized to 50% width
    expect(fill.style.width).toBe('50%');
  });

  it('handles extreme positive score (1.0)', () => {
    render(<SentimentBar score={1.0} label="Very Positive" />);
    
    const fill = screen.getByTestId('sentiment-bar-fill');
    expect(fill.style.width).toBe('100%');
    expect(screen.getByTestId('sentiment-score')).toHaveTextContent('1.00');
  });

  it('handles extreme negative score (-1.0)', () => {
    render(<SentimentBar score={-1.0} label="Very Negative" />);
    
    const fill = screen.getByTestId('sentiment-bar-fill');
    expect(fill.style.width).toBe('0%');
    expect(screen.getByTestId('sentiment-score')).toHaveTextContent('-1.00');
  });

  it('displays formatted score with two decimal places', () => {
    render(<SentimentBar score={0.123456} label="Test" />);
    
    expect(screen.getByTestId('sentiment-score')).toHaveTextContent('0.12');
  });
});
