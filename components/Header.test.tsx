import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Header } from './Header';

describe('Header', () => {
  it('renders the header with the correct title', () => {
    render(<Header />);
    expect(screen.getByText('Political Social Media Tracker')).toBeInTheDocument();
  });
});