import axios from "axios";
import type { ApiResponse } from "../types";

const BASE_URL = "http://localhost:8000";

export async function sendMessage(characterId: number, message: string): Promise<ApiResponse> {
  const { data } = await axios.post<ApiResponse>(
    `${BASE_URL}/characters/${characterId}/talk/`,
    { message }
  );
  return data;
}
