import { renderHook, act } from '@testing-library/react';
import { useSocialMediaTracker } from './useSocialMediaTracker';
import { INITIAL_LEADERS } from '../constants';
import * as api from '../services/api';

// Mock the fetchPostsFromBackend function
vi.mock('../services/api');

describe('useSocialMediaTracker', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should handle errors when fetching posts for a leader', async () => {
    const { result } = renderHook(() => useSocialMediaTracker());
    const leaderToRefresh = INITIAL_LEADERS[0];

    // Mock the API to throw an error
    const mockedApi = vi.mocked(api);
    mockedApi.fetchPostsFromBackend.mockRejectedValue(new Error('API Error'));

    await act(async () => {
      await result.current.fetchPostsForLeader(leaderToRefresh.id);
    });

    expect(result.current.error).toBe(`Failed to refresh posts for ${leaderToRefresh.name}.`);
    expect(result.current.isLoading).toBe(false);
  });
});