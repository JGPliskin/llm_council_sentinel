import { ReactNode } from 'react';

export type AgentId = 'kant' | 'kojima' | 'nietzsche' | 'confucius' | 'chair';
export type SimulationStage = 'idle' | 'stage1' | 'stage2' | 'stage3';

export interface AgentProfile {
  id: AgentId;
  name: string;
  fullName: string;
  avatar: string;
  role: string;
  color: string;
}

export interface AgentResponse {
  title: string;
  content: string[];
}

export interface PeerReview {
  id: number;
  from: AgentId;
  to: AgentId;
  comment: string;
  type: 'criticism' | 'suggestion' | 'rhetoric';
}

export interface LogStep {
  id: number;
  agentId: AgentId;
  text: string;
  status: 'pending' | 'processing' | 'complete';
  time: string;
}

export interface Ranking {
  id: AgentId;
  score: number;
  rank: number;
}
