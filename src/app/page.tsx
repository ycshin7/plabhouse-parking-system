'use client';
import { useState } from 'react';
import MainPage from '@/components/MainPage';
import AdminPage from '@/components/AdminPage';

export default function App() {
    const [page, setPage] = useState<'main' | 'admin'>('main');
    if (page === 'admin') return <AdminPage onBack={() => setPage('main')} />;
    return <MainPage onAdmin={() => setPage('admin')} />;
}
