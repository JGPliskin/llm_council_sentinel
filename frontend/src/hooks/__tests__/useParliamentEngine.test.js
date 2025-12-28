import { renderHook, act } from '@testing-library/react';
import { useParliamentEngine } from '../../hooks/useParliamentEngine';
import { api } from '../../api';
import { vi, describe, it, expect, beforeEach } from 'vitest';

// Fix for resolved_councilors usage in hook
// Hook expects event.resolved_councilors to init progress
vi.mock('../../api', () => ({
    api: {
        createConversation: vi.fn(),
        sendMessageStream: vi.fn(),
    }
}));

describe('useParliamentEngine', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('initializes with idle stage', () => {
        const { result } = renderHook(() => useParliamentEngine());
        expect(result.current.stage).toBe('idle');
        expect(result.current.isLoading).toBe(false);
    });

    it('starts session correctly', async () => {
        const mockConv = { id: '123' };
        api.createConversation.mockResolvedValue(mockConv);

        const { result } = renderHook(() => useParliamentEngine());

        await act(async () => {
            await result.current.startSession("Hello", ['agent1']);
        });

        expect(result.current.stage).toBe('stage1');
        expect(result.current.isLoading).toBe(true);
        expect(api.createConversation).toHaveBeenCalled();
        expect(api.sendMessageStream).toHaveBeenCalledWith(
            '123', "Hello", expect.any(Function), ['agent1'], true
        );
    });

    it('handles META event to set resolved councilors', async () => {
        const mockConv = { id: '123' };
        api.createConversation.mockResolvedValue(mockConv);

        // Capture the callback passed to sendMessageStream
        let streamCallback;
        api.sendMessageStream.mockImplementation(async (id, prompt, cb) => {
            streamCallback = cb;
        });

        const { result } = renderHook(() => useParliamentEngine());

        await act(async () => {
            await result.current.startSession("Hi", []);
        });

        // Simulate META event
        act(() => {
            streamCallback('meta', {
                resolved_councilors: [{ id: 'c1', name: 'C1' }]
            });
        });

        expect(result.current.resolvedCouncilors).toHaveLength(1);
        expect(result.current.resolvedCouncilors[0].id).toBe('c1');
    });

    it('accumulates thinking steps', async () => {
        const mockConv = { id: '123' };
        api.createConversation.mockResolvedValue(mockConv);
        let streamCallback;
        api.sendMessageStream.mockImplementation(async (_, __, cb) => { streamCallback = cb; });

        const { result } = renderHook(() => useParliamentEngine());
        await act(() => result.current.startSession("Hi", []));

        // Simulate Stage 1 Thinking
        act(() => {
            streamCallback('thinking', {
                stage: 'stage1',
                councilor_id: 'c1',
                delta: 'Thought process...',
                t: 1.0
            });
        });

        expect(result.current.thinkingSteps).toHaveLength(1);
        expect(result.current.thinkingSteps[0].text).toBe('Thought process...');
    });

    it('transitions to Stage 2', async () => {
        const mockConv = { id: '123' };
        api.createConversation.mockResolvedValue(mockConv);
        let streamCallback;
        api.sendMessageStream.mockImplementation(async (_, __, cb) => { streamCallback = cb; });

        const { result } = renderHook(() => useParliamentEngine());
        await act(() => result.current.startSession("Hi", []));

        act(() => {
            streamCallback('stage2_start', { skipped: false });
        });

        expect(result.current.stage).toBe('stage2');
    });
});
