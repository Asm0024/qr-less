import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { LogIn, User } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { login, register, type LoginRequest, type RegisterRequest } from '@/api/auth';
import { toast } from '@/components/ui/sonner';

interface AuthFormProps {
  mode: 'login' | 'register';
  onModeChange: (mode: 'login' | 'register') => void;
}

export const AuthForm: React.FC<AuthFormProps> = ({ mode, onModeChange }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const queryClient = useQueryClient();

  const loginMutation = useMutation({
    mutationFn: (credentials: LoginRequest) => login(credentials),
    onSuccess: (user) => {
      queryClient.setQueryData(['user'], user);
      toast.success("Success", {
        description: "Logged in successfully!",
      });
    },
    onError: () => {
      toast.error("Error", {
        description: "Invalid credentials",
      });
    },
  });

  const registerMutation = useMutation({
    mutationFn: (credentials: RegisterRequest) => register(credentials),
    onSuccess: (user) => {
      queryClient.setQueryData(['user'], user);
      toast.success('Success', {
        description: "Account created successfully!",
      });
    },
    onError: () => {
      toast.error("Error", {
        description: "Failed to create account",
      });
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!username.trim() || !password.trim()) {
      toast.error("Error", {
        description: "Please fill in all fields",
      });
      return;
    }

    if (mode === 'login') {
      loginMutation.mutate({ username, password });
    } else {
      registerMutation.mutate({ username, password });
    }
  };

  const isLoading = loginMutation.isPending || registerMutation.isPending;

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="text-center">
        <CardTitle className="flex items-center justify-center gap-2">
          {mode === 'login' ? <LogIn className="h-5 w-5" /> : <User className="h-5 w-5" />}
          {mode === 'login' ? 'Welcome Back' : 'Create Account'}
        </CardTitle>
        <CardDescription>
          {mode === 'login'
            ? 'Sign in to your account to generate QR codes'
            : 'Create a new account to get started'
          }
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="username">Username</Label>
            <Input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your username"
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
            />
          </div>
          <Button
            type="submit"
            className="w-full"
            disabled={isLoading}
          >
            {isLoading ? 'Please wait...' : (mode === 'login' ? 'Sign In' : 'Create Account')}
          </Button>
        </form>
        <div className="mt-4 text-center">
          <Button
            variant="link"
            onClick={() => onModeChange(mode === 'login' ? 'register' : 'login')}
            className="text-sm"
          >
            {mode === 'login'
              ? "Don't have an account? Sign up"
              : "Already have an account? Sign in"
            }
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};