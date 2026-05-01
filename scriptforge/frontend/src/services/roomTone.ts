import api from '../lib/api';

export interface RoomToneItem {
  id: string;
  name: string;
  description: string | null;
  core_rules: string;
  forbidden_topics: string | null;
  is_preset: boolean;
}

export async function listRoomTones(): Promise<{ total: number; items: RoomToneItem[] }> {
  const { data } = await api.get('/room-tones/');
  return data;
}

export async function getRoomTone(id: string): Promise<RoomToneItem> {
  const { data } = await api.get(`/room-tones/${id}`);
  return data;
}
