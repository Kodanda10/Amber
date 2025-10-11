const DEVANAGARI_DIGITS: Record<string, string> = {
  '0': '०',
  '1': '१',
  '2': '२',
  '3': '३',
  '4': '४',
  '5': '५',
  '6': '६',
  '7': '७',
  '8': '८',
  '9': '९',
};

const HINDI_MONTHS = [
  'जनवरी',
  'फ़रवरी',
  'मार्च',
  'अप्रैल',
  'मई',
  'जून',
  'जुलाई',
  'अगस्त',
  'सितंबर',
  'अक्तूबर',
  'नवंबर',
  'दिसंबर',
];

export const toDevanagariDigits = (value: string): string =>
  value.replace(/[0-9]/g, digit => DEVANAGARI_DIGITS[digit]);

export const format_date_in_hindi = (date: Date): string => {
  const day = String(date.getDate()).padStart(2, '0');
  const month = HINDI_MONTHS[date.getMonth()];
  const year = String(date.getFullYear());
  return `${toDevanagariDigits(day)} ${month} ${toDevanagariDigits(year)}`;
};

const LANGUAGE_LABELS: Record<string, string> = {
  hi: 'हिन्दी',
  'hi-in': 'हिन्दी',
  en: 'English',
  'en-in': 'English',
};

export const getLanguageLabel = (rawCode: string | null | undefined): string | undefined => {
  if (!rawCode) return undefined;
  const code = rawCode.toLowerCase();
  if (LANGUAGE_LABELS[code]) {
    return LANGUAGE_LABELS[code];
  }
  const [base] = code.split('-');
  return LANGUAGE_LABELS[base];
};
