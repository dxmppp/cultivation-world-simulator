import { httpClient } from '../http';

export interface CreatePlayerParams {
  name: string;
  gender: string;
  age: number;
  initial_realm: string;
  sect_id?: string;
  persona_ids?: string[];
  backstory?: string;
}

export interface PlayerCommandParams {
  command: string;
  player_avatar_id: string;
}

export interface PlayerStatusDTO {
  id: string;
  name: string;
  is_player: boolean;
  realm: string;
  hp: number;
  hp_max: number;
  mp: number;
  position: { x: number; y: number };
  subordinates: { id: string; name: string; realm: string }[];
  friends: { id: string; name: string; realm: string }[];
  pending_commands_count: number;
}

export interface PlayerListDTO {
  players: { id: string; name: string; realm: string }[];
}

export interface CommandResultDTO {
  status: 'ok' | 'error';
  message: string;
  action_name?: string;
  params?: Record<string, unknown>;
}

export const playerApi = {
  /**
   * 创建玩家角色
   */
  createPlayer(params: CreatePlayerParams) {
    return httpClient.post<{ status: string; avatar_id: string; name: string; realm: string }>(
      '/api/player/create',
      params
    );
  },

  /**
   * 提交玩家指令（自然语言）
   */
  submitCommand(params: PlayerCommandParams) {
    return httpClient.post<CommandResultDTO>('/api/player/command', params);
  },

  /**
   * 获取玩家角色状态
   */
  getPlayerStatus(avatarId: string) {
    return httpClient.get<PlayerStatusDTO>(`/api/player/status/${avatarId}`);
  },

  /**
   * 列出所有玩家角色
   */
  listPlayers() {
    return httpClient.get<PlayerListDTO>('/api/player/list');
  },
};
