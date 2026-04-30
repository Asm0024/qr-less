import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { authApi } from '@/api/auth';

interface User {
  id: string;
  username: string;
}

interface LoginRequest {
  username: string;
  password: string;
}

interface RegisterRequest {
  username: string;
  password: string;
}

export const useAuth = () => {
  const queryClient = useQueryClient();

  const { data: user } = useQuery({
    queryKey: ['user'],
    queryFn: authApi.getCurrentUser,
    staleTime: Infinity,
  });

  const loginMutation = useMutation({
    mutationFn: (credentials: LoginRequest) => authApi.login(credentials),
    onSuccess: (user) => {
      queryClient.setQueryData(['user'], user);
    },
  });

  const registerMutation = useMutation({
    mutationFn: (credentials: RegisterRequest) => authApi.register(credentials),
    onSuccess: (user) => {
      queryClient.setQueryData(['user'], user);
    },
  });

  const logout = () => {
    authApi.logout();
    queryClient.setQueryData(['user'], null);
  };

  return {
    user,
    login: loginMutation.mutateAsync,
    register: registerMutation.mutateAsync,
    logout,
    isLoading: loginMutation.isPending || registerMutation.isPending,
  };
};
