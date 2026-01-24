export interface Character {
  id: string;
  name: string;
  role: string;
  avatarUrl: string; // Square icon for cards
  standingUrl: string; // Tall full-body image for the stage
  description: string;
  systemInstruction: string;
  themeColor: string; // Hex color for highlights
  status: 'ONLINE' | 'OFFLINE' | 'BUSY';
}

export interface Message {
  id: string;
  role: 'user' | 'model';
  content: string;
  timestamp: number;
}

export interface LogEntry {
  id: string;
  code: string;
  title: string;
  active: boolean;
}