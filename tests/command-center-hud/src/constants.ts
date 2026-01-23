import { Councilor, Chairman } from './types';

export const CHAIRMAN: Chairman = {
  id: 'chairman',
  name: 'OVERSEER',
  role: 'Consensus Arbiter',
  description: '最终裁决者。负责综合各方观点，消除分歧，输出最具可操作性的共识方案。',
  avatarUrl: 'https://picsum.photos/id/64/200/200' // Placeholder
};

export const COUNCILORS: Councilor[] = [
  {
    id: 'immanuel_kant',
    name: 'KANT',
    role: 'Ethics Guardian',
    description: '严谨的逻辑卫士。擅长通过伦理框架与先验逻辑审查内容，捕捉潜在的逻辑谬误与道德风险。',
    avatarUrl: 'https://picsum.photos/id/338/300/400'
  },
  {
    id: 'donald_trump',
    name: 'TRUMP',
    role: 'Market Strategist',
    description: '直觉敏锐的策略家。关注市场情绪与宏观博弈，擅长用非传统视角打破思维定势，提供激进的行动建议。',
    avatarUrl: 'https://picsum.photos/id/177/300/400'
  },
  {
    id: 'hideo_kojima',
    name: 'KOJIMA',
    role: 'Narrative Weaver',
    description: '深邃的叙事架构师。能够解构复杂的信息流，将其重组为具有电影质感与哲学深度的连贯叙事。',
    avatarUrl: 'https://picsum.photos/id/433/300/400'
  }
];