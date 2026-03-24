export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  isLoading?: boolean;
}

export interface ProjectFile {
  path: string;
  content: string;
}

export interface Project {
  id: string;
  name: string;
  board: string;
  description: string;
  files: ProjectFile[];
  createdAt: number;
}

export type Board = 'arduino:avr:uno' | 'arduino:avr:nano' | 'arduino:mbed_rp2040:pico' | 'esp32:esp32:esp32';

export interface LLMConfig {
  apiKey: string;
  baseUrl: string;
  model: string;
}
