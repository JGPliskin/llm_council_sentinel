import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import App from '../App';
import { api } from '../api';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import React from 'react';
import { MemoryRouter } from 'react-router-dom';

// Mock API
vi.mock('../api', () => ({
    api: {
        listConversations: vi.fn().mockResolvedValue([]),
        getCouncilors: vi.fn().mockResolvedValue([
            { id: 'c1', name: 'Councilor 1', model: 'gpt-4' }
        ]),
        createConversation: vi.fn(),
        sendMessageStream: vi.fn(),
        getConversation: vi.fn(),
    }
}));

// Mock scrollIntoView
window.HTMLElement.prototype.scrollIntoView = function () { };

describe('App Integration Flow (Simulated E2E)', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('completes a full session flow', async () => {
        const mockConv = { id: 'conv_123' };
        api.createConversation.mockResolvedValue(mockConv);

        // Capture SSE callback
        let streamCallback;
        api.sendMessageStream.mockImplementation(async (id, prompt, cb) => {
            streamCallback = cb;
        });

        await act(async () => {
            render(
                <MemoryRouter>
                    <App />
                </MemoryRouter>
            );
        });

        // 1. Verify Welcome Screen
        expect(screen.getByText(/System Online/i)).toBeInTheDocument();

        // 2. Start Session (Click Input)
        const input = screen.getByPlaceholderText(/Enter directive.../i);
        fireEvent.change(input, { target: { value: 'Test Directive' } });

        const startBtn = screen.getByRole('button', { name: /^Init$/i });
        await act(async () => {
            fireEvent.click(startBtn);
        });

        // Verify API calls
        expect(api.createConversation).toHaveBeenCalled();
        expect(api.sendMessageStream).toHaveBeenCalled();

        // 3. Simulate META event (Resolved Councilors)
        await act(async () => {
            streamCallback('meta', {
                resolved_councilors: [{ id: 'c1', name: 'Councilor 1', avatar: 'C1' }]
            });
        });

        // HUD should appear (Stage 1)
        expect(screen.getAllByText('Councilor 1').length).toBeGreaterThan(0); // In Tab or HUD

        // 4. Simulate Stage 1 Thinking + Answer Stream
        await act(async () => {
            streamCallback('thinking', {
                stage: 'stage1',
                councilor_id: 'c1',
                bullet_id: 'b1',
                title: 'Analyze',
                detail: 'Detail',
                op: 'append',
                t: 0.5
            });
            streamCallback('stage1_answer_delta', {
                councilor_id: 'c1',
                delta: 'My '
            });
            streamCallback('stage1_answer_delta', {
                councilor_id: 'c1',
                delta: 'Proposal'
            });
        });

        expect(screen.getByText(/Thinking Process/i)).toBeInTheDocument();
        expect(screen.getByText('My Proposal')).toBeInTheDocument();

        // 5. Simulate Stage 1 Item
        await act(async () => {
            streamCallback('stage1_item', {
                data: {
                    councilor_id: 'c1',
                    answer_markdown: 'My Proposal',
                    status: 'ok'
                }
            });
        });

        // Check content
        expect(screen.getByText('My Proposal')).toBeInTheDocument();

        // 6. Simulate Stage 2 (Peer Review)
        await act(async () => {
            streamCallback('stage2_start', {});
            streamCallback('stage2_complete', {
                data: {
                    reviews: [],
                    anon_map: { 'anon_1': 'c1' }
                }
            });
        });

        // 7. Simulate Stage 3 (Consensus)
        await act(async () => {
            streamCallback('stage3_start', {});
            streamCallback('stage3_complete', {
                data: {
                    title: 'Final Decision',
                    content: 'Agreed.'
                }
            });
        });

        // Beacon should be present (Consensus Unlocked)
        // Since we don't have easy selector for beacon animation, check for "Consensus" Tab availability
        const consensusTab = screen.getByRole('button', { name: /Consensus/i });
        expect(consensusTab).not.toBeDisabled();

        // Click Consensus
        await act(async () => {
            fireEvent.click(consensusTab);
        });

        expect(screen.getByText('Final Decision')).toBeInTheDocument();
    });
});
