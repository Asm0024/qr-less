import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AuthForm } from '@/components/AuthForm';
import { QRGenerator } from '@/components/QRGenerator';
import { Header } from '@/components/Header';
import { getCurrentUser } from '@/api/auth';
import { HistoryList } from '@/components/HistoryList';

const Index = () => {
    const { data: user } = useQuery({
        queryKey: ['user'],
        queryFn: getCurrentUser,
        staleTime: Infinity,
    });
    const [authMode, setAuthMode] = useState<'login' | 'register'>('login');

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
            <Header />

            <main className="container mx-auto px-4 py-8">
                {user ? (
                    <div className="space-y-8">
                        <div className="flex justify-center">
                            <QRGenerator />
                        </div>
                        <HistoryList />
                    </div>
                ) : (
                    <div className="flex justify-center items-center min-h-[60vh]">
                        <AuthForm mode={authMode} onModeChange={setAuthMode} />
                    </div>
                )}
            </main>
        </div>
    );
};

export default Index;