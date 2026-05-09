export interface Message {
  role: "user" | "character";
  text: string;
}

export interface ApiResponse {
  character: string;
  response: string;
}
