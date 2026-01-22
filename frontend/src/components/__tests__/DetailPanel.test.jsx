import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { DetailPanel } from '../DetailPanel';

describe('DetailPanel Mobile Drawer', () => {
    const mockProps = {
        stage: 'stage1',
        activeTab: 'test',
        evaluationComments: {},
        synthesisSteps: [],
        stage2ThinkingByJudge: null,
        stage2AnonMap: {},
        aggregateRankings: [],
        stage2Skipped: false,
        onClose: vi.fn(),
        userPrompt: 'Test user question?',
        isPanelFullscreen: false,
        onToggleFullscreen: vi.fn(),
    };

    it('should render drag handle on mobile', () => {
        render(<DetailPanel {...mockProps} />);
        // Drag handle should be present
        const dragHandle = document.querySelector('.md\\:hidden');
        expect(dragHandle).toBeTruthy();
    });

    it('should display user prompt in Stage 1', () => {
        render(<DetailPanel {...mockProps} />);
        expect(screen.getByText('Test user question?')).toBeTruthy();
    });

    it('should show fullscreen button only in Stage 3', () => {
        const { rerender } = render(<DetailPanel {...mockProps} stage="stage1" />);
        expect(screen.queryByTitle('Fullscreen')).toBeNull();

        rerender(<DetailPanel {...mockProps} stage="stage3" />);
        expect(screen.queryByTitle('Fullscreen')).toBeTruthy();
    });

    it('should toggle fullscreen when button clicked', () => {
        const onToggleFullscreen = vi.fn();
        render(<DetailPanel {...mockProps} stage="stage3" onToggleFullscreen={onToggleFullscreen} />);

        const fullscreenButton = screen.getByTitle('Fullscreen');
        fireEvent.click(fullscreenButton);

        expect(onToggleFullscreen).toHaveBeenCalledTimes(1);
    });

    it('should call onClose when close button clicked', () => {
        const onClose = vi.fn();
        render(<DetailPanel {...mockProps} onClose={onClose} />);

        const closeButton = screen.getByTitle('Close Panel');
        fireEvent.click(closeButton);

        expect(onClose).toHaveBeenCalledTimes(1);
    });
});
