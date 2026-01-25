import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import TacticalHUD from '../TacticalHUD';

// Mock UnitDeckList as it is tested separately
vi.mock('../UnitDeckList', () => ({
    UnitDeckList: ({ items, onItemClick }) => (
        <div data-testid="unit-deck-list">
            {items.map(item => (
                <div
                    key={item.id}
                    data-testid={`deck-item-${item.id}`}
                    data-state={item.state}
                    data-progress={item.progress}
                    data-rank={item.rank}
                    onClick={() => onItemClick(item.id)}
                >
                    {item.name}
                </div>
            ))}
        </div>
    )
}));

describe('TacticalHUD Integration', () => {
    const mockCouncilors = [
        { id: 'c1', name: 'C1', role: 'R1' },
        { id: 'c2', name: 'C2', role: 'R2' }
    ];

    it('renders Resolved Councilors Only', () => {
        render(
            <TacticalHUD
                stage="stage1"
                resolvedCouncilors={[mockCouncilors[0]]} // Only C1 resolved
                agentProgress={{ c1: 50 }}
                allCouncilors={mockCouncilors}
            />
        );

        expect(screen.getByTestId('deck-item-c1')).toBeInTheDocument();
        expect(screen.queryByTestId('deck-item-c2')).not.toBeInTheDocument();
    });

    it('Stage 1/2: Passes Progress', () => {
        render(
            <TacticalHUD
                stage="stage1"
                resolvedCouncilors={mockCouncilors}
                agentProgress={{ c1: 50, c2: 100 }}
                allCouncilors={mockCouncilors}
            />
        );

        const item1 = screen.getByTestId('deck-item-c1');
        expect(item1).toHaveAttribute('data-progress', '50');
    });

    it('Stage 3: Hides Progress, Shows Rank', () => {
        render(
            <TacticalHUD
                stage="stage3"
                resolvedCouncilors={mockCouncilors}
                aggregateRankings={[{ councilor_id: 'c1', rank: 1 }, { councilor_id: 'c2', rank: 2 }]}
                allCouncilors={mockCouncilors}
                agentProgress={{ c1: 50 }} // Should be ignored
            />
        );

        const item1 = screen.getByTestId('deck-item-c1');
        expect(item1).toHaveAttribute('data-progress', '0'); // Progress should be 0 or hidden
        expect(item1).toHaveAttribute('data-rank', '1');
    });

    it('Stage 2 Skipped: Sets State to Skipped', () => {
        render(
            <TacticalHUD
                stage="stage2"
                stage2Skipped={true}
                resolvedCouncilors={mockCouncilors}
                agentProgress={{}}
                allCouncilors={mockCouncilors}
            />
        );

        const item1 = screen.getByTestId('deck-item-c1');
        expect(item1).toHaveAttribute('data-state', 'skipped');
    });
});
