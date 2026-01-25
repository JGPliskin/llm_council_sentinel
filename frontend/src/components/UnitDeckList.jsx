import React from 'react';
import { UnitDeckCard } from './UnitDeckCard';

/**
 * UnitDeckList
 * 
 * Pure presentation container for the deck of cards.
 * Handles layout strategies:
 * - Desktop: Grid layout (md:grid-cols-3)
 * - Mobile: Flex horizontal scroll (snap-x)
 */
export const UnitDeckList = ({
    items = [],
    onItemClick,
    onItemHover
}) => {
    return (
        <div className="w-full flex items-center justify-center">
            <div
                className={`
                    w-full max-w-7xl mx-auto
                    grid gap-1 md:gap-4 lg:gap-8 pb-1 md:pb-0 px-2 md:px-0
                    items-center justify-center
                    ${items.length === 1 ? 'grid-cols-1 w-[80%]' : ''}
                    ${items.length === 2 ? 'grid-cols-2' : ''}
                    ${items.length >= 3 ? 'grid-cols-3' : ''}
                `}
            >
                {items.map((item) => (
                    <UnitDeckCard
                        key={item.id}
                        data={item}
                        onClick={onItemClick}
                        onHover={onItemHover}
                        totalItems={items.length}
                    />
                ))}
            </div>
        </div >
    );
};
