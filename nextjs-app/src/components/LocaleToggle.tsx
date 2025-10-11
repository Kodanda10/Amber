/**
 * L10N-003: Locale Toggle Component
 * Allows users to switch between English and Hindi locales
 */
import React, { useState, useEffect } from 'react';

export type Locale = 'en' | 'hi';

interface LocaleToggleProps {
  initialLocale?: Locale;
  onChange?: (locale: Locale) => void;
}

export const LocaleToggle: React.FC<LocaleToggleProps> = ({ initialLocale = 'en', onChange }) => {
  const [locale, setLocale] = useState<Locale>(initialLocale);

  useEffect(() => {
    // Load from localStorage on mount
    const saved = localStorage.getItem('locale') as Locale | null;
    if (saved && (saved === 'en' || saved === 'hi')) {
      setLocale(saved);
    }
  }, []);

  const handleToggle = () => {
    const newLocale: Locale = locale === 'en' ? 'hi' : 'en';
    setLocale(newLocale);
    localStorage.setItem('locale', newLocale);
    onChange?.(newLocale);
  };

  return (
    <div data-testid="locale-toggle-container">
      <button
        onClick={handleToggle}
        data-testid="locale-toggle-button"
        className="flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
        aria-label={`Switch to ${locale === 'en' ? 'Hindi' : 'English'}`}
      >
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {locale === 'en' ? '🇬🇧 English' : '🇮🇳 हिन्दी'}
        </span>
      </button>
      <span data-testid="current-locale" className="sr-only">
        {locale}
      </span>
    </div>
  );
};
