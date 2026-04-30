
import React from 'react';
import { Button } from '@/components/ui/button';
import { LogIn, User, QrCode } from 'lucide-react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { getCurrentUser, logout } from '@/api/auth';

export const Header: React.FC = () => {
  const queryClient = useQueryClient();
  const { data: user } = useQuery({
    queryKey: ['user'],
    queryFn: getCurrentUser,
    staleTime: Infinity,
  });

  const handleLogout = () => {
    logout();
    queryClient.setQueryData(['user'], null);
  };

  return (
    <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <QrCode className="h-6 w-6 text-primary" />
          <h1 className="text-xl font-bold">QR Generator</h1>
        </div>

        {user && (
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <User className="h-4 w-4" />
              <span className="text-sm font-medium">{user.username}</span>
            </div>
            <Button variant="outline" size="sm" onClick={handleLogout}>
              <LogIn className="h-4 w-4 mr-2" />
              Logout
            </Button>
          </div>
        )}
      </div>
    </header>
  );
};
