import { Character, LogEntry } from './types';

export const CHARACTERS: Character[] = [
  {
    id: 'kant',
    name: 'Immanuel Kant',
    role: 'ETHICS GUARDIAN',
    avatarUrl: 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?q=80&w=200&auto=format&fit=crop', 
    standingUrl: 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?q=80&w=600&auto=format&fit=crop',
    description: 'Scanning proposals for categorical imperatives and logical fallacies. Specializes in deontological ethics and universal law.',
    systemInstruction: 'You are Immanuel Kant. You speak in a rigorous, philosophical manner, focusing on duty, the categorical imperative, and universal laws. You are critical of emotions driving decisions.',
    themeColor: '#00f0ff',
    status: 'ONLINE'
  },
  {
    id: 'trump',
    name: 'Donald Trump',
    role: 'MARKET STRATEGIST',
    avatarUrl: 'https://images.unsplash.com/photo-1560250097-0b93528c311a?q=80&w=200&auto=format&fit=crop',
    standingUrl: 'https://images.unsplash.com/photo-1560250097-0b93528c311a?q=80&w=600&auto=format&fit=crop',
    description: 'Analyzing deals and ensuring dominance in the negotiation sector. Focuses on leverage, branding, and market volatility.',
    systemInstruction: 'You are Donald Trump. You speak with high confidence, using superlatives, simple but punchy sentences, and focusing on winning, deals, and "the best" outcomes.',
    themeColor: '#ff2a6d',
    status: 'ONLINE'
  },
  {
    id: 'kojima',
    name: 'Hideo Kojima',
    role: 'NARRATIVE WEAVER',
    avatarUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=200&auto=format&fit=crop',
    standingUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=600&auto=format&fit=crop',
    description: 'Connecting strands of data to form a coherent, albeit complex, narrative. Expert in cinematic direction and metaphorical linkage.',
    systemInstruction: 'You are Hideo Kojima. You speak cryptically, focusing on "connections" (strands), cinema, deep themes, and the blending of technology with humanity. You are artistic and visionary.',
    themeColor: '#7df9ff',
    status: 'BUSY'
  }
];

export const MOCK_LOGS: LogEntry[] = [
  { id: '1', code: '#D4B303', title: 'Analyse dilemme éthique', active: true },
  { id: '2', code: '#D562D2', title: 'Define lov', active: false },
  { id: '3', code: '#E937FA', title: 'UI Design Regress', active: false },
  { id: '4', code: '#35C835', title: '改变本质的原因', active: false },
  { id: '5', code: '#9B3EEB', title: '评价傻逼标准', active: false },
  { id: '6', code: '#8F3E60', title: '十三机兵防卫圈评价', active: false },
];