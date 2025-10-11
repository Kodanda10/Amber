/**
 * FE-CORE-002: Infinite Scroll Stabilization Tests
 * Tests for the useInfiniteScroll hook in Dashboard component
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, waitFor } from '@testing-library/react';
import React, { useRef } from 'react';

// Create a test component that uses the infinite scroll logic
function TestInfiniteScroll({
  enabled,
  onLoadMore,
  loading,
}: {
  enabled: boolean;
  onLoadMore: () => void;
  loading: boolean;
}) {
  const sentinelRef = useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (!enabled || !sentinelRef.current || !onLoadMore) return;
    const el = sentinelRef.current;
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting && !loading) {
            onLoadMore();
          }
        }
      },
      { root: null, rootMargin: '200px', threshold: 0 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [enabled, onLoadMore, loading]);

  return (
    <div>
      <div data-testid="content">Content</div>
      <div ref={sentinelRef} data-testid="sentinel">
        Loading sentinel
      </div>
    </div>
  );
}

describe('FE-CORE-002: Infinite Scroll', () => {
  let mockObserve: ReturnType<typeof vi.fn>;
  let mockUnobserve: ReturnType<typeof vi.fn>;
  let mockDisconnect: ReturnType<typeof vi.fn>;
  let observerCallback: IntersectionObserverCallback | null;

  beforeEach(() => {
    observerCallback = null;
    mockObserve = vi.fn();
    mockUnobserve = vi.fn();
    mockDisconnect = vi.fn();

    // Mock IntersectionObserver with callback capture
    global.IntersectionObserver = vi.fn().mockImplementation((callback, options) => {
      observerCallback = callback;
      return {
        observe: mockObserve,
        unobserve: mockUnobserve,
        disconnect: mockDisconnect,
        root: null,
        rootMargin: options?.rootMargin || '',
        thresholds: Array.isArray(options?.threshold) ? options.threshold : [options?.threshold || 0],
        takeRecords: () => [],
      };
    }) as any;
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('creates IntersectionObserver when enabled', () => {
    const onLoadMore = vi.fn();
    
    render(
      <TestInfiniteScroll enabled={true} onLoadMore={onLoadMore} loading={false} />
    );

    expect(IntersectionObserver).toHaveBeenCalledTimes(1);
    expect(IntersectionObserver).toHaveBeenCalledWith(
      expect.any(Function),
      expect.objectContaining({
        root: null,
        rootMargin: '200px',
        threshold: 0,
      })
    );
  });

  it('observes sentinel element when enabled', () => {
    const onLoadMore = vi.fn();
    
    const { getByTestId } = render(
      <TestInfiniteScroll enabled={true} onLoadMore={onLoadMore} loading={false} />
    );

    expect(mockObserve).toHaveBeenCalledTimes(1);
    expect(mockObserve).toHaveBeenCalledWith(getByTestId('sentinel'));
  });

  it('does not create observer when disabled', () => {
    const onLoadMore = vi.fn();
    
    render(
      <TestInfiniteScroll enabled={false} onLoadMore={onLoadMore} loading={false} />
    );

    expect(IntersectionObserver).not.toHaveBeenCalled();
    expect(mockObserve).not.toHaveBeenCalled();
  });

  it('calls onLoadMore when sentinel intersects and not loading', async () => {
    const onLoadMore = vi.fn();
    
    render(
      <TestInfiniteScroll enabled={true} onLoadMore={onLoadMore} loading={false} />
    );

    // Simulate intersection
    if (observerCallback) {
      const mockEntry: IntersectionObserverEntry = {
        isIntersecting: true,
        target: document.createElement('div'),
        boundingClientRect: {} as DOMRectReadOnly,
        intersectionRatio: 1,
        intersectionRect: {} as DOMRectReadOnly,
        rootBounds: null,
        time: Date.now(),
      };

      observerCallback([mockEntry], {} as IntersectionObserver);
    }

    await waitFor(() => {
      expect(onLoadMore).toHaveBeenCalledTimes(1);
    });
  });

  it('does not call onLoadMore when loading', async () => {
    const onLoadMore = vi.fn();
    
    render(
      <TestInfiniteScroll enabled={true} onLoadMore={onLoadMore} loading={true} />
    );

    // Simulate intersection
    if (observerCallback) {
      const mockEntry: IntersectionObserverEntry = {
        isIntersecting: true,
        target: document.createElement('div'),
        boundingClientRect: {} as DOMRectReadOnly,
        intersectionRatio: 1,
        intersectionRect: {} as DOMRectReadOnly,
        rootBounds: null,
        time: Date.now(),
      };

      observerCallback([mockEntry], {} as IntersectionObserver);
    }

    // Wait a bit to ensure callback isn't called
    await new Promise((resolve) => setTimeout(resolve, 100));

    expect(onLoadMore).not.toHaveBeenCalled();
  });

  it('does not call onLoadMore when not intersecting', async () => {
    const onLoadMore = vi.fn();
    
    render(
      <TestInfiniteScroll enabled={true} onLoadMore={onLoadMore} loading={false} />
    );

    // Simulate non-intersection
    if (observerCallback) {
      const mockEntry: IntersectionObserverEntry = {
        isIntersecting: false,
        target: document.createElement('div'),
        boundingClientRect: {} as DOMRectReadOnly,
        intersectionRatio: 0,
        intersectionRect: {} as DOMRectReadOnly,
        rootBounds: null,
        time: Date.now(),
      };

      observerCallback([mockEntry], {} as IntersectionObserver);
    }

    // Wait a bit to ensure callback isn't called
    await new Promise((resolve) => setTimeout(resolve, 100));

    expect(onLoadMore).not.toHaveBeenCalled();
  });

  it('disconnects observer on cleanup', () => {
    const onLoadMore = vi.fn();
    
    const { unmount } = render(
      <TestInfiniteScroll enabled={true} onLoadMore={onLoadMore} loading={false} />
    );

    expect(mockDisconnect).not.toHaveBeenCalled();

    unmount();

    expect(mockDisconnect).toHaveBeenCalledTimes(1);
  });

  it('recreates observer when dependencies change', () => {
    const onLoadMore = vi.fn();
    
    const { rerender } = render(
      <TestInfiniteScroll enabled={true} onLoadMore={onLoadMore} loading={false} />
    );

    expect(IntersectionObserver).toHaveBeenCalledTimes(1);
    expect(mockDisconnect).not.toHaveBeenCalled();

    // Change loading state
    rerender(
      <TestInfiniteScroll enabled={true} onLoadMore={onLoadMore} loading={true} />
    );

    // Should disconnect old observer and create new one
    expect(mockDisconnect).toHaveBeenCalled();
    expect(IntersectionObserver).toHaveBeenCalledTimes(2);
  });

  it('handles multiple entries in intersection callback', async () => {
    const onLoadMore = vi.fn();
    
    render(
      <TestInfiniteScroll enabled={true} onLoadMore={onLoadMore} loading={false} />
    );

    // Simulate multiple entries, only one intersecting
    if (observerCallback) {
      const mockEntry1: IntersectionObserverEntry = {
        isIntersecting: false,
        target: document.createElement('div'),
        boundingClientRect: {} as DOMRectReadOnly,
        intersectionRatio: 0,
        intersectionRect: {} as DOMRectReadOnly,
        rootBounds: null,
        time: Date.now(),
      };

      const mockEntry2: IntersectionObserverEntry = {
        isIntersecting: true,
        target: document.createElement('div'),
        boundingClientRect: {} as DOMRectReadOnly,
        intersectionRatio: 1,
        intersectionRect: {} as DOMRectReadOnly,
        rootBounds: null,
        time: Date.now(),
      };

      observerCallback([mockEntry1, mockEntry2], {} as IntersectionObserver);
    }

    await waitFor(() => {
      expect(onLoadMore).toHaveBeenCalledTimes(1);
    });
  });
});
