import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { InfoPanel } from '../InfoPanel';
import { CommandInput } from '../CommandInput';
import { CouncilorCard } from '../CouncilorCard';
import { describe, it, expect, vi } from 'vitest';

describe('InfoPanel', () => {
    const mockData = {
        id: 'c1',
        name: 'Test Councilor',
        role: 'Tester',
        description: 'A test description.'
    };

    it('renders data correctly', () => {
        render(<InfoPanel data={mockData} />);
        expect(screen.getByText('UNIT: Test Councilor')).toBeDefined();
        expect(screen.getByText('// Tester')).toBeDefined();
        expect(screen.getByText('A test description.')).toBeDefined();
    });

    it('updates when data changes', () => {
        vi.useFakeTimers();
        const { rerender } = render(<InfoPanel data={mockData} />);
        expect(screen.getByText('UNIT: Test Councilor')).toBeDefined();

        const newData = { ...mockData, id: 'c2', name: 'New Name' };
        rerender(<InfoPanel data={newData} />);

        // Fast forward timer
        act(() => {
            vi.advanceTimersByTime(200);
        });

        expect(screen.getByText('UNIT: New Name')).toBeDefined();
        vi.useRealTimers();
    });
});

describe('CommandInput', () => {
    it('renders input and button', () => {
        render(<CommandInput value="" onChange={() => { }} onEngage={() => { }} isReady={true} />);
        expect(screen.getByPlaceholderText(/Enter directive/i)).toBeDefined();
        expect(screen.getByText('Engage')).toBeDefined();
    });

    it('handles input change', () => {
        const handleChange = vi.fn();
        render(<CommandInput value="" onChange={handleChange} onEngage={() => { }} isReady={true} />);
        const input = screen.getByPlaceholderText(/Enter directive/i);
        fireEvent.change(input, { target: { value: 'start' } });
        expect(handleChange).toHaveBeenCalledWith('start');
    });

    it('handles preset click', () => {
        const handleEngage = vi.fn();
        const handleChange = vi.fn();
        // Mock Presets are rendered
        render(<CommandInput value="" onChange={handleChange} onEngage={handleEngage} isReady={true} />);

        const shieldPreset = screen.getByText('Philosophy Shield');
        fireEvent.click(shieldPreset);

        expect(handleChange).toHaveBeenCalled();
        expect(handleEngage).toHaveBeenCalled();
    });
});

describe('CouncilorCard', () => {
    const mockData = {
        id: 'c1',
        name: 'Test',
        avatar: '/test.png'
    };

    it('renders correctly', () => {
        render(
            <CouncilorCard
                data={mockData}
                isSelected={false}
                isFocused={false}
                onToggle={() => { }}
            />
        );
        expect(screen.getByText('Test')).toBeDefined();
        expect(screen.getByText('OFFLINE')).toBeDefined();
    });

    it('shows ONLINE when selected', () => {
        render(
            <CouncilorCard
                data={mockData}
                isSelected={true}
                isFocused={false}
                onToggle={() => { }}
            />
        );
        expect(screen.getByText('ONLINE')).toBeDefined();
    });

    it('triggers toggle on click', () => {
        const handleToggle = vi.fn();
        render(
            <CouncilorCard
                data={mockData}
                isSelected={false}
                isFocused={false}
                onToggle={handleToggle}
            />
        );
        fireEvent.click(screen.getByText('Test'));
        expect(handleToggle).toHaveBeenCalledWith('c1');
    });
});
