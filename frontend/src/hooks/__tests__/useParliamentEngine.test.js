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

    it('accumulates thinking steps per councilor', async () => {
        const mockConv = { id: '123' };
        api.createConversation.mockResolvedValue(mockConv);
        let streamCallback;
        api.sendMessageStream.mockImplementation(async (_, __, cb) => { streamCallback = cb; });

        const { result } = renderHook(() => useParliamentEngine());
        await act(() => result.current.startSession("Hi", []));

        // Simulate Stage 1 Thinking (append)
        act(() => {
            streamCallback('thinking', {
                stage: 'stage1',
                councilor_id: 'c1',
                bullet_id: 'b1',
                title: 'Thought process...',
                detail: 'Detail line',
                op: 'append',
                t: 1.0
            });
        });

        expect(result.current.thinkingByCouncilor.c1.steps).toHaveLength(1);
        expect(result.current.thinkingByCouncilor.c1.steps[0].title).toBe('Thought process...');
    });

    it('updates thinking steps by bullet_id', async () => {
        const mockConv = { id: '123' };
        api.createConversation.mockResolvedValue(mockConv);
        let streamCallback;
        api.sendMessageStream.mockImplementation(async (_, __, cb) => { streamCallback = cb; });

        const { result } = renderHook(() => useParliamentEngine());
        await act(() => result.current.startSession("Hi", []));

        act(() => {
            streamCallback('thinking', {
                stage: 'stage1',
                councilor_id: 'c1',
                bullet_id: 'b1',
                title: 'Initial',
                detail: 'First',
                op: 'append',
                t: 1.0
            });
            streamCallback('thinking', {
                stage: 'stage1',
                councilor_id: 'c1',
                bullet_id: 'b1',
                title: 'Updated',
                detail: 'Second',
                op: 'update',
                t: 1.5
            });
        });

        const step = result.current.thinkingByCouncilor.c1.steps[0];
        expect(step.title).toBe('Updated');
        expect(step.detail).toBe('Second');
    });

    it('streams stage1 answer delta', async () => {
        const mockConv = { id: '123' };
        api.createConversation.mockResolvedValue(mockConv);
        let streamCallback;
        api.sendMessageStream.mockImplementation(async (_, __, cb) => { streamCallback = cb; });

        const { result } = renderHook(() => useParliamentEngine());
        await act(() => result.current.startSession("Hi", []));

        act(() => {
            streamCallback('stage1_answer_delta', {
                councilor_id: 'c1',
                delta: 'Hello '
            });
            streamCallback('stage1_answer_delta', {
                councilor_id: 'c1',
                delta: 'World'
            });
        });

        expect(result.current.stage1AnswerStream.c1).toBe('Hello World');
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

    it('restores thinking from conversation metadata', () => {
        const { result } = renderHook(() => useParliamentEngine());

        const conv = {
            id: 'conv_1',
            messages: [
                {
                    role: 'assistant',
                    stage1: [{ councilor_id: 'c1', status: 'ok', answer_markdown: 'Done' }],
                    metadata: {
                        thinking: {
                            stage1: {
                                c1: {
                                    status: 'done',
                                    steps: [{ bullet_id: 'b1', title: 'Step', detail: 'Detail', t: 1.2 }]
                                }
                            }
                        }
                    }
                }
            ],
            metadata: {
                resolved_councilors: [{ id: 'c1', name: 'C1' }]
            }
        };

        act(() => {
            result.current.loadSession(conv);
        });

        expect(result.current.thinkingByCouncilor.c1.steps[0].title).toBe('Step');
        expect(result.current.thinkingExpanded.c1).toBe(true);
    });
});
