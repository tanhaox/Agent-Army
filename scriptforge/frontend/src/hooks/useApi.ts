import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';

export function useApiQuery<T>(key: string[], url: string, params?: object) {
  return useQuery({
    queryKey: key,
    queryFn: async () => {
      const { data } = await api.get<T>(url, { params });
      return data;
    },
  });
}

export function useApiMutation<T, B = unknown>(url: string, method: 'post' | 'put' | 'patch' = 'post') {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (body: B) => {
      const { data } = await api[method]<T>(url, body);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries();
    },
  });
}
