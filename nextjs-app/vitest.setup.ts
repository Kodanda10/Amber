import '@testing-library/jest-dom';

// FE-CORE-002: Mock IntersectionObserver for infinite scroll tests
global.IntersectionObserver = class IntersectionObserver {
  constructor(
    public callback: IntersectionObserverCallback,
    public options?: IntersectionObserverInit
  ) {}

  observe() {
    // Mock observe method
  }

  unobserve() {
    // Mock unobserve method
  }

  disconnect() {
    // Mock disconnect method
  }

  takeRecords(): IntersectionObserverEntry[] {
    return [];
  }

  readonly root: Element | null = null;
  readonly rootMargin: string = '';
  readonly thresholds: readonly number[] = [];
} as any;

