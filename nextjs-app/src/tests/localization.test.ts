
import { describe, it, expect } from 'vitest';
import { format_date_in_hindi } from '../utils/localization';

describe('L10N-001: Hindi Date Formatting', () => {
  it('should format a date into a Devanagari script string', () => {
    const testDate = new Date(2025, 9, 4); // Month is 0-indexed, so 9 is October
    const expectedOutput = '०४ अक्तूबर २०२५';
    expect(format_date_in_hindi(testDate)).toBe(expectedOutput);
  });
});
