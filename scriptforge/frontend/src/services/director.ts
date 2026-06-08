import api from '../lib/api';
import type { DirectorRole, DirectorAct } from '../types';

export const directorService = {
  saveRoles: (scriptId: string, roles: DirectorRole[]) =>
    api.post(`/scripts/${scriptId}/director/roles`, { roles }),

  getRoles: (scriptId: string) =>
    api.get<{ script_id: string; roles: DirectorRole[] }>(`/scripts/${scriptId}/director/roles`),

  saveActs: (scriptId: string, acts: DirectorAct[]) =>
    api.post(`/scripts/${scriptId}/director/acts`, { acts }),

  getActs: (scriptId: string) =>
    api.get<{ script_id: string; acts: DirectorAct[] }>(`/scripts/${scriptId}/director/acts`),

  clearAll: (scriptId: string) =>
    api.delete(`/scripts/${scriptId}/director/all`),
};
