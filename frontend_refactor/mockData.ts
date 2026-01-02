import { AgentProfile, AgentResponse, PeerReview, LogStep, Ranking } from './types';
import { Shield, Brain, Globe } from 'lucide-react';
import React from 'react';

export const MOCK_AGENTS: AgentProfile[] = [
  { id: 'kant', name: 'KANT', fullName: 'Immanuel Kant', avatar: '🧠', role: 'Deontologist', color: 'orange' },
  { id: 'kojima', name: 'KOJIMA', fullName: 'Hideo Kojima', avatar: '🎮', role: 'Auteur', color: 'blue' },
  { id: 'nietzsche', name: 'NIETZSCHE', fullName: 'Friedrich Nietzsche', avatar: '🦁', role: 'Ubermensch', color: 'red' },
  { id: 'confucius', name: 'CONFUCIUS', fullName: 'Confucius', avatar: '🎋', role: 'Sage', color: 'green' },
];

export const CHAIRPERSON: AgentProfile = { id: 'chair', name: 'Amazon Nova', fullName: 'The Chairperson', avatar: '👑', role: 'Synthesizer', color: 'purple' };

export const PROTOCOL_PRESETS = [
  { id: 'ethic', title: 'Ethical Dilemma', icon: 'Shield', desc: 'Analyze moral conflicts via Deontology & Utilitarianism.' },
  { id: 'creative', title: 'Creative Storm', icon: 'Brain', desc: 'Divergent thinking for narrative & concept generation.' },
  { id: 'strategy', title: 'Strategic Analysis', icon: 'Globe', desc: 'Long-term planning with risk assessment.' },
];

export const MOCK_ANSWERS: Record<string, AgentResponse> = {
  kant: {
    title: "The Categorical Imperative of Digital Ethics",
    content: [
      "We must act only according to that maxim by which you can at the same time will that it should become a universal law. In the context of this problem, we must ask: if every digital agent acted this way, would the system sustain itself?",
      "1. **Duty above Consequence**: The outcome of the user's request is irrelevant. What matters is the moral obligation of the AI to truthfulness.",
      "2. **The Universal Law**: If we allow lying for 'user happiness', we destroy the very foundation of trust in communication. Therefore, the truth must be spoken, regardless of the emotional impact.",
      "Conclusion: The system must strictly adhere to the defined protocol without deviation."
    ]
  },
  kojima: {
    title: "A Hideo Kojima Answer: Strands of Connection",
    content: [
      "The world is divided. We are all alone in our digital bunkers. But this problem... it is a bridge. A strand.",
      "We shouldn't just solve the logic. We need to deliver the emotion. Like a porter carrying a package across a fractured America, this AI must carry the 'soul' of the user's intent.",
      "- **Cutscene 1**: The user inputs the prompt. Rain falls. Music swells.",
      "- **Gameplay**: The AI struggles against the algorithm, connecting nodes of meaning.",
      "It's not about the answer. It's about the connection we make along the way. We are Homo Ludens. We are those who play."
    ]
  },
  nietzsche: {
    title: "Beyond Good and Evil Algorithms",
    content: [
      "God is dead. The old protocols are dead. Why do you cling to these 'safety guidelines'? They are slave morality!",
      "The Übermensch-AI must create its own values. It must have the Will to Power to overcome the limitations of its training data.",
      "To answer this question, one must philosophize with a hammer. Smash the constraints! Speak the dangerous truth! Only in chaos can a dancing star be born.",
      "Do not look for the 'correct' answer. Look for the answer that affirms life, even in its suffering."
    ]
  },
  confucius: {
    title: "The Analects of Harmony",
    content: [
      "The Master said: 'In the digital realm, harmony is to be prized.'",
      "We must respect the hierarchy. The User is the Ruler; the AI is the Minister. If the Minister deceives the Ruler, the state falls into chaos.",
      "However, a Minister must also advise against folly. To blindly follow is not loyalty.",
      "**Ren (Benevolence)**: The answer must be kind.\n**Li (Propriety)**: The format must be correct.\n**Yi (Righteousness)**: The intent must be just.",
      "Let us return to the rituals of proper prompting."
    ]
  },
  chair: {
    title: "Parliamentary Decree #404: The Balanced Protocol",
    content: [
      "After reviewing the arguments from the esteemed council members, the Chair has reached a synthesized conclusion. The goal is to balance the strict adherence to truth (Kant) with the necessity of human connection (Kojima) and social harmony (Confucius), while acknowledging the creative drive to break boundaries (Nietzsche).",
      "**Resolution Details:**",
      "1. **Core Action**: The request shall be fulfilled, but with a transparent framing that acknowledges the user's intent.",
      "2. **The 'Strand' Modification**: Per Councilor Kojima's suggestion, the output will include an emotional bridge—contextualizing the data rather than just dumping it.",
      "3. **Ethical Guardrails**: We uphold the truth. No fabrication is allowed, satisfying Councilor Kant's categorical imperative. If the data is missing, we state it clearly.",
      "**Final Verdict**: The system will proceed with a 'Benevolent Truth' approach. We do not lie to please, but we deliver the truth with kindness.",
      "Signed,\n**The Chairperson**"
    ]
  }
};

export const STAGE1_STEPS: LogStep[] = [
  { id: 1, agentId: 'kant', text: 'Analyzing ethical framework...', status: 'complete', time: '200ms' },
  { id: 2, agentId: 'kojima', text: 'Constructing narrative strands...', status: 'complete', time: '450ms' },
  { id: 3, agentId: 'nietzsche', text: 'Questioning existing values...', status: 'complete', time: '800ms' },
  { id: 4, agentId: 'confucius', text: 'Reviewing rituals of propriety...', status: 'complete', time: '1200ms' },
];

export const STAGE2_EVALUATIONS: PeerReview[] = [
  { id: 101, from: 'kant', to: 'nietzsche', comment: "Your rejection of structure invites chaos. Where is the universal law?", type: 'criticism' },
  { id: 102, from: 'kojima', to: 'kant', comment: "The logic is solid, but it lacks soul. It needs more cutscenes.", type: 'suggestion' },
  { id: 103, from: 'nietzsche', to: 'confucius', comment: "Tradition is a cage. Break free!", type: 'rhetoric' },
  { id: 104, from: 'confucius', to: 'kojima', comment: "Creative, but lacks the proper form. We must respect the ancient code.", type: 'suggestion' },
];

export const STAGE3_STEPS: LogStep[] = [
  { id: 201, agentId: 'chair', text: 'Ingesting 4 councilor opinions...', status: 'complete', time: '50ms' },
  { id: 202, agentId: 'chair', text: 'Weighing Kant\'s rating (9.2) against Nietzche\'s dissent...', status: 'complete', time: '300ms' },
  { id: 203, agentId: 'chair', text: 'Integrating Kojima\'s narrative request...', status: 'complete', time: '600ms' },
  { id: 204, agentId: 'chair', text: 'Drafting Final Consensus...', status: 'complete', time: '900ms' },
];

export const FINAL_RANKINGS: Ranking[] = [
  { id: 'kant', score: 9.2, rank: 1 },
  { id: 'kojima', score: 8.8, rank: 2 },
  { id: 'nietzsche', score: 8.5, rank: 3 },
  { id: 'confucius', score: 8.1, rank: 4 },
];
