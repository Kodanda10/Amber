/**
 * L10N-003: Toggle Locale Preference Tests
 * Tests for locale preference toggle and persistence
 */
import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { LocaleToggle, type Locale } from './LocaleToggle';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('L10N-003: Locale Toggle', () => {
  beforeEach(() => {
    localStorageMock.clear();
  });

  it('renders with default English locale', () => {
    render(<LocaleToggle />);
    
    expect(screen.getByTestId('locale-toggle-container')).toBeInTheDocument();
    expect(screen.getByTestId('locale-toggle-button')).toHaveTextContent('🇬🇧 English');
  });

  it('toggles from English to Hindi on click', () => {
    render(<LocaleToggle />);
    
    const button = screen.getByTestId('locale-toggle-button');
    fireEvent.click(button);
    
    expect(button).toHaveTextContent('🇮🇳 हिन्दी');
  });

  it('toggles from Hindi back to English on second click', () => {
    render(<LocaleToggle />);
    
    const button = screen.getByTestId('locale-toggle-button');
    fireEvent.click(button); // en -> hi
    fireEvent.click(button); // hi -> en
    
    expect(button).toHaveTextContent('🇬🇧 English');
  });

  it('persists locale preference to localStorage', () => {
    render(<LocaleToggle />);
    
    const button = screen.getByTestId('locale-toggle-button');
    fireEvent.click(button);
    
    expect(localStorage.getItem('locale')).toBe('hi');
  });

  it('loads saved locale from localStorage on mount', () => {
    localStorage.setItem('locale', 'hi');
    
    render(<LocaleToggle />);
    
    expect(screen.getByTestId('locale-toggle-button')).toHaveTextContent('🇮🇳 हिन्दी');
  });

  it('calls onChange callback when toggled', () => {
    const onChange = vi.fn();
    render(<LocaleToggle onChange={onChange} />);
    
    const button = screen.getByTestId('locale-toggle-button');
    fireEvent.click(button);
    
    expect(onChange).toHaveBeenCalledWith('hi');
  });

  it('calls onChange multiple times for multiple toggles', () => {
    const onChange = vi.fn();
    render(<LocaleToggle onChange={onChange} />);
    
    const button = screen.getByTestId('locale-toggle-button');
    fireEvent.click(button); // en -> hi
    fireEvent.click(button); // hi -> en
    fireEvent.click(button); // en -> hi
    
    expect(onChange).toHaveBeenCalledTimes(3);
    expect(onChange).toHaveBeenNthCalledWith(1, 'hi');
    expect(onChange).toHaveBeenNthCalledWith(2, 'en');
    expect(onChange).toHaveBeenNthCalledWith(3, 'hi');
  });

  it('uses initialLocale prop when no saved preference exists', () => {
    render(<LocaleToggle initialLocale="hi" />);
    
    expect(screen.getByTestId('locale-toggle-button')).toHaveTextContent('🇮🇳 हिन्दी');
  });

  it('saved preference overrides initialLocale prop', () => {
    localStorage.setItem('locale', 'hi');
    
    render(<LocaleToggle initialLocale="en" />);
    
    expect(screen.getByTestId('locale-toggle-button')).toHaveTextContent('🇮🇳 हिन्दी');
  });

  it('has accessible aria-label that changes with locale', () => {
    render(<LocaleToggle />);
    
    const button = screen.getByTestId('locale-toggle-button');
    expect(button).toHaveAttribute('aria-label', 'Switch to Hindi');
    
    fireEvent.click(button);
    expect(button).toHaveAttribute('aria-label', 'Switch to English');
  });
});
