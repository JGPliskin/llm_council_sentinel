import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { UnitDeckCard } from '../UnitDeckCard';

describe('UnitDeckCard', () => {
    const mockData = {
        id: 'test_agent',
        name: 'Test Agent',
        role: 'Tester',
        avatar: '/avatars/test.png',
        state: 'standby',
        progress: 0,
        isActiveTab: false
    };

    it('renders basic info correctly', () => {
        render(<UnitDeckCard data={mockData} />);
        expect(screen.getByText('Test Agent')).toBeInTheDocument();
        expect(screen.getByText('// Tester')).toBeInTheDocument();
        expect(screen.getByText('STANDBY')).toBeInTheDocument();
    });

    it('renders Linked state correctly', () => {
        const linkedData = { ...mockData, state: 'linked' };
        render(<UnitDeckCard data={linkedData} />);
        expect(screen.getByText('LINKED')).toBeInTheDocument();
        // Check for specific styling class or element if needed, e.g. "shimmer" div
        const card = screen.getByRole('button');
        expect(card).toHaveClass('bg-[rgba(6,182,212,0.1)]');
    });

    it('renders Skipped state correctly', () => {
        const skippedData = { ...mockData, state: 'skipped' };
        render(<UnitDeckCard data={skippedData} />);
        expect(screen.getByText('SKIPPED')).toBeInTheDocument();
    });

    it('renders Rank Badge when rank is present', () => {
        const rankedData = { ...mockData, rank: 1 };
        render(<UnitDeckCard data={rankedData} />);
        expect(screen.getByText('#1')).toBeInTheDocument();
    });

    it('calls onClick with id when clicked', () => {
        const handleClick = vi.fn();
        render(<UnitDeckCard data={mockData} onClick={handleClick} />);

        fireEvent.click(screen.getByRole('button'));
        expect(handleClick).toHaveBeenCalledWith('test_agent');
    });

    it('calls onHover with id/null on mouse enter/leave', () => {
        const handleHover = vi.fn();
        render(<UnitDeckCard data={mockData} onHover={handleHover} />);

        const card = screen.getByRole('button');
        fireEvent.mouseEnter(card);
        expect(handleHover).toHaveBeenCalledWith('test_agent');

        fireEvent.mouseLeave(card);
        expect(handleHover).toHaveBeenCalledWith(null);
    });
});
