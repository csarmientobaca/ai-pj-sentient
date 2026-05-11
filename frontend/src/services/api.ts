import axios from "axios";
import type { ApiResponse, AuthTokens, Character, UserProfile } from "../types";
import { tokens } from "./tokens";

const BASE_URL = "http://localhost:8000";

const api = axios.create({ baseURL: BASE_URL });

api.interceptors.request.use((config) => {
  const token = tokens.getAccess();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;

    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refresh = tokens.getRefresh();

      if (refresh) {
        try {
          const { data } = await axios.post<AuthTokens>(`${BASE_URL}/auth/refresh/`, {
            refresh,
          });
          tokens.set(data.access, refresh);
          original.headers.Authorization = `Bearer ${data.access}`;
          return api(original);
        } catch {
          tokens.clear();
          window.location.href = "/login";
        }
      } else {
        window.location.href = "/login";
      }
    }

    return Promise.reject(error);
  }
);

export async function register(username: string, password: string): Promise<void> {
  await axios.post(`${BASE_URL}/auth/register/`, { username, password });
}

export async function login(username: string, password: string): Promise<AuthTokens> {
  const { data } = await axios.post<AuthTokens>(`${BASE_URL}/auth/login/`, { username, password });
  return data;
}

export async function getCharacters(): Promise<Character[]> {
  const { data } = await api.get<Character[]>("/characters/");
  return data;
}

export async function createCharacter(
  name: string,
  personality: string,
  description: string
): Promise<Character> {
  const { data } = await api.post<Character>("/characters/create/", {
    name,
    personality,
    description,
  });
  return data;
}

export async function getProfile(): Promise<UserProfile> {
  const { data } = await api.get<UserProfile>("/auth/profile/");
  return data;
}

export async function saveApiKey(apiKey: string): Promise<void> {
  await api.post("/auth/api-key/", { api_key: apiKey });
}

export async function sendMessage(characterId: number, message: string): Promise<ApiResponse> {
  const { data } = await api.post<ApiResponse>(`/characters/${characterId}/talk/`, { message });
  return data;
}
