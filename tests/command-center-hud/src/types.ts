export interface Councilor {
  id: string;
  name: string;
  role: string;
  description: string;
  avatarUrl: string;
}

export interface Chairman {
  id: string;
  name: string;
  role: string;
  description: string;
  avatarUrl: string;
}

export type ViewMode = 'desktop' | 'mobile';