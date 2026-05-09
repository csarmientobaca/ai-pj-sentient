import axios from "axios";
import type { ApiResponse, AuthTokens, Character, UserProfile } from "../types";

const BASE_URL = "http://localhost:8000";

function authHeader() {
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function register(username: string, password: string): Promise<void> {
  await axios.post(`${BASE_URL}/auth/register/`, { username, password });
}

export async function login(username: string, password: string): Promise<AuthTokens> {
  const { data } = await axios.post<AuthTokens>(`${BASE_URL}/auth/login/`, { username, password });
  return data;
}

export async function getCharacters(): Promise<Character[]> {
  const { data } = await axios.get<Character[]>(`${BASE_URL}/characters/`, {
    headers: authHeader(),
  });
  return data;
}

export async function createCharacter(
  name: string,
  personality: string,
  description: string
): Promise<Character> {
  const { data } = await axios.post<Character>(
    `${BASE_URL}/characters/create/`,
    { name, personality, description },
    { headers: authHeader() }
  );
  return data;
}

export async function getProfile(): Promise<UserProfile> {
  const { data } = await axios.get<UserProfile>(`${BASE_URL}/auth/profile/`, {
    headers: authHeader(),
  });
  return data;
}

export async function saveApiKey(apiKey: string): Promise<void> {
  await axios.post(`${BASE_URL}/auth/api-key/`, { api_key: apiKey }, { headers: authHeader() });
}

export async function sendMessage(characterId: number, message: string): Promise<ApiResponse> {
  const { data } = await axios.post<ApiResponse>(
    `${BASE_URL}/characters/${characterId}/talk/`,
    { message },
    { headers: authHeader() }
  );
  return data;
}
