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
            <div className="
                w-full max-w-7xl mx-auto
                flex flex-nowrap overflow-x-auto snap-x snap-mandatory 
                md:grid md:grid-cols-3 
                gap-3 md:gap-4 lg:gap-8 
                pb-1 md:pb-0 
                no-scrollbar scroll-smooth
                px-4 md:px-0
            ">
                {items.map((item) => (
                    <UnitDeckCard
                        key={item.id}
                        data={item}
                        onClick={onItemClick}
                        onHover={onItemHover}
                    />
                ))}
            </div>
        </div>
    );
};
