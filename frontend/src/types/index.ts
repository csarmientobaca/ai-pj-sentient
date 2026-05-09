export interface Message {
  role: "user" | "character";
  text: string;
}

export interface ApiResponse {
  character: string;
  response: string;
}

export interface Character {
  id: number;
  name: string;
  mood: string;
  description: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface UserProfile {
  username: string;
  has_own_key: boolean;
  trial_interactions_used: number;
  trial_limit: number;
  trial_remaining: number;
}
