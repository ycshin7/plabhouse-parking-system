'use client';

import { useState, useEffect, useMemo } from 'react';
import { User, RequestsData, HistoryEntry } from '@/types';
import * as XLSX from 'xlsx';

function getKSTDateString() {
    const now = new Date();
    const utc = now.getTime() + (now.getTimezoneOffset() * 60000);
    const kst = new Date(utc + 9 * 60 * 60 * 1000);
    return kst.toISOString().split('T')[0];
}

interface AdminPageProps {
    onBack: () => void;
}

export default function AdminPage({ onBack }: AdminPageProps) {
    const [data, setData] = useState<{ users: User[]; requests: RequestsData; history: HistoryEntry[] } | null>(null);
    const [activeTab, setActiveTab] = useState<'result' | 'users' | 'history' | 'data'>('result');
    const [loading, setLoading] = useState(true);
    const [adminKey, setAdminKey] = useState('');
    const [showKeyInput, setShowKeyInput] = useState(false);

    // User Management State
    const [editingUserIndex, setEditingUserIndex] = useState<number | null>(null);
    const [editUserForm, setEditUserForm] = useState<Partial<User>>({});
    const [isAddingUser, setIsAddingUser] = useState(false);
    const [newUser, setNewUser] = useState<Partial<User>>({ car_type: 'SEDAN' });

    // History Management State
    const [editingHistoryDate, setEditingHistoryDate] = useState<string | null>(null);
    const [editHistoryForm, setEditHistoryForm] = useState<Partial<HistoryEntry>>({});
    const [historyFilter, setHistoryFilter] = useState({ start: '', end: '' });
    const [isAddingHistory, setIsAddingHistory] = useState(false);
    const [newHistoryForm, setNewHistoryForm] = useState<Partial<HistoryEntry>>({ date: '', admin: [], tower: [], wait: [] });
    const [githubCheckResult, setGithubCheckResult] = useState<any>(null);
    const [isCheckingGithub, setIsCheckingGithub] = useState(false);

    const fetchData = async () => {
        try {
            const res = await fetch('/api/data', { cache: 'no-store' });
            const json = await res.json();
            setData(json);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    // Calculate Last Parked Date for each user from history
    const usersWithLastParked = useMemo(() => {
        if (!data) return [];
        return data.users.map(user => {
            let lastDate = '-';
            for (const h of data.history) {
                const combined = [...h.admin, ...h.tower];
                if (combined.some(item => item.split(' (')[0] === user.name)) {
                    lastDate = h.date;
                    break;
                }
            }
            return { ...user, calculated_last_parked: lastDate };
        });
    }, [data]);

    const handleAllocate = async () => {
        if (!adminKey) {
            setShowKeyInput(true);
            return;
        }
        try {
            const res = await fetch('/api/allocate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ adminKey }),
            });
            const json = await res.json();
            if (res.ok) {
                alert('배정이 완료되었습니다!');
                fetchData();
                setShowKeyInput(false);
            } else {
                alert(json.error || '배정 중 오류 발생');
            }
        } catch (e) {
            alert('네트워크 오류');
        }
    };

    const handleSendSlack = async (date: string) => {
        if (!adminKey) {
            setShowKeyInput(true);
            return;
        }
        try {
            const res = await fetch('/api/slack', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ date, adminKey }),
            });
            const json = await res.json();
            if (res.ok) {
                alert('슬랙 알림을 전송했습니다!');
                fetchData();
            } else {
                alert(json.error || '전송 중 오류 발생');
            }
        } catch (e) {
            alert('네트워크 오류');
        }
    };

    const handleAddUser = async () => {
        if (!newUser.name) return;
        const res = await fetch('/api/users', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newUser),
        });
        if (res.ok) {
            setIsAddingUser(false);
            setNewUser({ car_type: 'SEDAN' });
            fetchData();
        } else {
            const json = await res.json();
            alert(json.error);
        }
    };

    const handleEditUser = async () => {
        if (editingUserIndex === null) return;
        const res = await fetch('/api/users', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ index: editingUserIndex, ...editUserForm }),
        });
        if (res.ok) {
            setEditingUserIndex(null);
            fetchData();
        } else {
            const json = await res.json();
            alert(json.error);
        }
    };

    const handleDeleteUser = async (index: number) => {
        if (!confirm('정말 삭제하시겠습니까?')) return;
        const res = await fetch('/api/users', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ index }),
        });
        if (res.ok) fetchData();
    };

    const handleAddHistory = async () => {
        if (!newHistoryForm.date) {
            alert('날짜를 입력해주세요.');
            return;
        }
        try {
            const res = await fetch('/api/history', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newHistoryForm),
            });
            const json = await res.json();
            if (res.ok) {
                setIsAddingHistory(false);
                setNewHistoryForm({ date: '', admin: [], tower: [], wait: [] });
                fetchData();
            } else {
                alert(json.error || '추가 중 오류 발생');
            }
        } catch (e) {
            alert('네트워크 오류');
        }
    };

    const handleUpdateHistory = async () => {
        if (!editingHistoryDate) return;
        const res = await fetch('/api/history', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(editHistoryForm),
        });
        if (res.ok) {
            setEditingHistoryDate(null);
            fetchData();
        } else {
            const json = await res.json();
            alert(json.error);
        }
    };

    const handleDeleteHistory = async (date: string) => {
        if (!confirm(`${date} 배정 내역을 삭제하시겠습니까?`)) return;
        const res = await fetch('/api/history', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ date }),
        });
        if (res.ok) fetchData();
    };

    const handleResetRequests = async () => {
        if (!confirm('오늘 신청 내역을 정말 초기화하시겠습니까?')) return;
        try {
            const res = await fetch('/api/apply', {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ reset: true }),
            });
            if (res.ok) {
                alert('신청 내역이 초기화되었습니다.');
                fetchData();
            }
        } catch (e) {
            alert('오류 발생');
        }
    };

    const handleCheckGithub = async () => {
        if (!adminKey) {
            setShowKeyInput(true);
            return;
        }
        setIsCheckingGithub(true);
        try {
            const res = await fetch('/api/github-check', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ adminKey }),
            });
            const json = await res.json();
            setGithubCheckResult(json);
        } catch (e) {
            alert('진단 중 오류 발생');
        } finally {
            setIsCheckingGithub(false);
        }
    };

    const downloadStaffExcel = () => {
        if (!usersWithLastParked) return;
        const exportData = usersWithLastParked.map(u => ({
            '이름': u.name,
            '차종': u.car_type,
            '차 번호': u.car_number || '',
            '상세 차종': u.car_details || '',
            '마지막 주차일': u.calculated_last_parked
        }));

        const ws = XLSX.utils.json_to_sheet(exportData);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "StaffList");
        XLSX.writeFile(wb, "staff_list.xlsx");
    };

    const filteredHistory = useMemo(() => {
        if (!data?.history) return [];
        let filtered = [...data.history];
        if (historyFilter.start) filtered = filtered.filter(h => h.date >= historyFilter.start);
        if (historyFilter.end) filtered = filtered.filter(h => h.date <= historyFilter.end);
        return filtered;
    }, [data?.history, historyFilter]);

    const tabs = [
        { id: 'result', label: '배정 결과' },
        { id: 'users', label: '직원 관리' },
        { id: 'history', label: '히스토리' },
        { id: 'data', label: '데이터 관리' },
    ] as const;

    if (loading) return <div className="flex h-screen items-center justify-center font-bold text-primary-500 animate-pulse">관리자 데이터 로드 중...</div>;

    return (
        <div className="mx-auto max-w-4xl min-h-screen pb-20 px-4">
            <header className="py-8 flex justify-between items-center">
                <h2 className="text-3xl font-extrabold tracking-tight text-ink">관리자 페이지</h2>
                <button
                    onClick={onBack}
                    className="btn-secondary rounded-full text-xs"
                >
                    <svg className="w-3.5 h-3.5 inline-block mr-1 -mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
                    메인으로
                </button>
            </header>

            {/* Tab Navigation */}
            <nav className="flex space-x-2 mb-8 p-1 bg-surface-muted rounded-input overflow-x-auto">
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex-1 min-w-[80px] py-2.5 rounded-tag text-xs font-bold transition-all ${activeTab === tab.id
                            ? 'bg-surface-card text-primary-500 shadow-sm'
                            : 'text-ink-tertiary hover:text-ink-secondary'
                            }`}
                    >
                        {tab.label}
                    </button>
                ))}
            </nav>

            {/* Admin Key Input */}
            {showKeyInput && (
                <div className="mb-6 p-4 card !rounded-input border-primary-100 animate-fade-in">
                    <label className="input-label text-primary-400 mb-2 block">Admin Key 입력</label>
                    <div className="flex gap-2">
                        <input
                            type="password"
                            placeholder="Admin Key를 입력하세요"
                            value={adminKey}
                            onChange={(e) => setAdminKey(e.target.value)}
                            className="input flex-1 text-sm"
                        />
                        <button
                            onClick={() => { setShowKeyInput(false); setAdminKey(''); }}
                            className="btn-ghost text-xs"
                        >
                            취소
                        </button>
                    </div>
                </div>
            )}

            <main className="animate-fade-in">
                {/* ================================
                    Result Tab
                    ================================ */}
                {activeTab === 'result' && (
                    <div className="space-y-6">
                        <div className="card">
                            <h3 className="section-title mb-6">오늘의 배정 현황</h3>
                            {data?.history[0]?.date === getKSTDateString() ? (
                                <div className="space-y-6">
                                    <div className="flex flex-col sm:flex-row gap-2">
                                        <div className="flex-1 p-4 bg-success-50 text-success-600 rounded-input font-bold text-center border border-success-100 flex items-center justify-center">
                                            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                                            오늘의 배정이 완료되었습니다.
                                        </div>
                                        <button
                                            onClick={() => handleSendSlack(data.history[0].date)}
                                            className="btn-secondary rounded-input flex items-center justify-center gap-2"
                                        >
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" /></svg>
                                            슬랙 알림 전송 {data.history[0].slack_notified && <span className="tag-blue text-[10px]">완료</span>}
                                        </button>
                                    </div>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="p-6 bg-primary-50/50 rounded-button border border-primary-100">
                                            <p className="section-label text-primary-500 mb-2">
                                                <svg className="w-3.5 h-3.5 inline-block mr-1 -mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>
                                                관리실
                                            </p>
                                            <div className="space-y-1">
                                                {data.history[0].admin.map(name => <p key={name} className="text-lg font-black text-ink">{name}</p>)}
                                                {data.history[0].admin.length === 0 && <p className="text-ink-placeholder">배정 없음</p>}
                                            </div>
                                        </div>
                                        <div className="p-6 bg-secondary-50/50 rounded-button border border-secondary-100">
                                            <p className="section-label text-secondary-500 mb-2">
                                                <svg className="w-3.5 h-3.5 inline-block mr-1 -mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" /></svg>
                                                타워
                                            </p>
                                            <div className="space-y-1">
                                                {data.history[0].tower.map(name => <p key={name} className="text-lg font-black text-ink">{name}</p>)}
                                                {data.history[0].tower.length === 0 && <p className="text-ink-placeholder">배정 없음</p>}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="text-center py-10">
                                    <svg className="w-12 h-12 mx-auto mb-4 text-ink-placeholder" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>
                                    <p className="text-ink-tertiary font-medium mb-8 text-sm">배정 결과가 아직 생성되지 않았습니다.</p>
                                    <button
                                        onClick={handleAllocate}
                                        className="btn-primary w-full"
                                    >
                                        배정 계산 수동 실행
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* ================================
                    Users Tab
                    ================================ */}
                {activeTab === 'users' && (
                    <div className="space-y-6">
                        <div className="flex justify-between items-center px-2">
                            <h3 className="section-title">직원 리스트 <span className="text-primary-500 text-sm ml-2">{data?.users.length}명</span></h3>
                            <div className="flex gap-2">
                                <button
                                    onClick={downloadStaffExcel}
                                    className="px-4 py-2 bg-success-50 text-success-600 rounded-tag text-[10px] font-bold flex items-center gap-1 border border-success-100"
                                >
                                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                                    엑셀 다운
                                </button>
                                <button
                                    onClick={() => setIsAddingUser(true)}
                                    className="px-4 py-2 bg-primary-500 text-white rounded-tag text-[10px] font-bold shadow-md shadow-primary-200"
                                >
                                    + 직원 추가
                                </button>
                            </div>
                        </div>

                        {(isAddingUser || editingUserIndex !== null) && (
                            <div className="card border-2 border-primary-200 animate-fade-in mb-8">
                                <h4 className="font-bold mb-6 text-primary-600">{isAddingUser ? '새 직원 등록' : '직원 정보 수정'}</h4>
                                <div className="space-y-4">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-1">
                                            <label className="input-label">이름</label>
                                            <input
                                                placeholder="이름"
                                                value={isAddingUser ? (newUser.name || '') : (editUserForm.name || '')}
                                                onChange={(e) => isAddingUser ? setNewUser({ ...newUser, name: e.target.value }) : setEditUserForm({ ...editUserForm, name: e.target.value })}
                                                className="input"
                                            />
                                        </div>
                                        <div className="space-y-1">
                                            <label className="input-label">차종</label>
                                            <select
                                                value={isAddingUser ? newUser.car_type : editUserForm.car_type}
                                                onChange={(e) => isAddingUser ? setNewUser({ ...newUser, car_type: e.target.value as any }) : setEditUserForm({ ...editUserForm, car_type: e.target.value as any })}
                                                className="select"
                                            >
                                                <option value="SEDAN">SEDAN (세단)</option>
                                                <option value="SUV">SUV (대형)</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-1">
                                            <label className="input-label">차 번호</label>
                                            <input
                                                placeholder="예: 12가 3456"
                                                value={isAddingUser ? (newUser.car_number || '') : (editUserForm.car_number || '')}
                                                onChange={(e) => isAddingUser ? setNewUser({ ...newUser, car_number: e.target.value }) : setEditUserForm({ ...editUserForm, car_number: e.target.value })}
                                                className="input"
                                            />
                                        </div>
                                        <div className="space-y-1">
                                            <label className="input-label">상세 차종</label>
                                            <input
                                                placeholder="예: 아반떼 CN7"
                                                value={isAddingUser ? (newUser.car_details || '') : (editUserForm.car_details || '')}
                                                onChange={(e) => isAddingUser ? setNewUser({ ...newUser, car_details: e.target.value }) : setEditUserForm({ ...editUserForm, car_details: e.target.value })}
                                                className="input"
                                            />
                                        </div>
                                    </div>
                                    <div className="flex gap-3 pt-4">
                                        <button
                                            onClick={isAddingUser ? handleAddUser : handleEditUser}
                                            className="btn-primary flex-1 py-3"
                                        >
                                            저장하기
                                        </button>
                                        <button
                                            onClick={() => { setIsAddingUser(false); setEditingUserIndex(null); }}
                                            className="flex-1 py-3 bg-surface-muted text-ink-tertiary rounded-button font-bold hover:bg-line-light transition-all"
                                        >
                                            취소
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )}

                        <div className="card !p-0 overflow-hidden overflow-x-auto">
                            <table className="w-full text-left border-collapse">
                                <thead>
                                    <tr className="bg-surface-muted border-b border-line-light">
                                        <th className="px-6 py-4 section-label">이름</th>
                                        <th className="px-6 py-4 section-label text-center">차종</th>
                                        <th className="px-6 py-4 section-label">차 번호</th>
                                        <th className="px-6 py-4 section-label">상세 차종</th>
                                        <th className="px-6 py-4 section-label">마지막 주차일</th>
                                        <th className="px-6 py-4 section-label text-center">관리</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {usersWithLastParked.map((user, idx) => (
                                        <tr key={user.name} className="border-b border-line-light last:border-0 hover:bg-surface-muted/30 transition-colors">
                                            <td className="px-6 py-4 font-bold text-ink text-sm">{user.name}</td>
                                            <td className="px-6 py-4 text-center">
                                                <span className={user.car_type === 'SUV' ? 'tag-purple text-[9px]' : 'tag-blue text-[9px]'}>
                                                    {user.car_type}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-xs text-ink-secondary font-medium">{user.car_number || '-'}</td>
                                            <td className="px-6 py-4 text-xs text-ink-secondary font-medium">{user.car_details || '-'}</td>
                                            <td className="px-6 py-4 text-xs text-primary-400 font-bold">{user.calculated_last_parked}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-center">
                                                <div className="flex items-center justify-center gap-2">
                                                    <button
                                                        onClick={() => {
                                                            setEditingUserIndex(idx);
                                                            setEditUserForm(user);
                                                            setIsAddingUser(false);
                                                        }}
                                                        className="w-8 h-8 flex items-center justify-center rounded-tag text-ink-placeholder hover:text-primary-500 hover:bg-primary-50 transition-all"
                                                    >
                                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                                                    </button>
                                                    <button
                                                        onClick={() => handleDeleteUser(idx)}
                                                        className="w-8 h-8 flex items-center justify-center rounded-tag text-ink-placeholder hover:text-danger-500 hover:bg-danger-50 transition-all"
                                                    >
                                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                            {data?.users.length === 0 && <div className="p-20 text-center text-ink-placeholder font-bold">등록된 직원이 없습니다.</div>}
                        </div>
                    </div>
                )}

                {/* ================================
                    History Tab
                    ================================ */}
                {activeTab === 'history' && (
                    <div className="space-y-6">
                        <div className="flex justify-between items-center px-2">
                            <h3 className="section-title">배정 레코드</h3>
                            <div className="flex items-center gap-3">
                                <div className="flex items-center gap-2 bg-surface-card px-4 py-2 rounded-input shadow-sm border border-line-light">
                                    <input
                                        type="date"
                                        className="text-[10px] outline-none font-bold text-ink-secondary"
                                        onChange={(e) => setHistoryFilter({ ...historyFilter, start: e.target.value })}
                                    />
                                    <span className="text-ink-placeholder">~</span>
                                    <input
                                        type="date"
                                        className="text-[10px] outline-none font-bold text-ink-secondary"
                                        onChange={(e) => setHistoryFilter({ ...historyFilter, end: e.target.value })}
                                    />
                                </div>
                                <button
                                    onClick={() => { setIsAddingHistory(true); setEditingHistoryDate(null); }}
                                    className="px-4 py-2 bg-primary-500 text-white rounded-tag text-[10px] font-bold shadow-md shadow-primary-200"
                                >
                                    + 수동 추가
                                </button>
                            </div>
                        </div>

                        {isAddingHistory && (
                            <div className="card border-2 border-primary-200 animate-fade-in">
                                <h4 className="font-bold mb-6 text-primary-600">주차이력 수동 추가</h4>
                                <div className="space-y-6">
                                    <div className="space-y-1">
                                        <label className="input-label">배정 날짜</label>
                                        <input
                                            type="date"
                                            value={newHistoryForm.date || ''}
                                            onChange={(e) => setNewHistoryForm({ ...newHistoryForm, date: e.target.value })}
                                            className="input"
                                        />
                                    </div>

                                    {['admin', 'tower', 'wait'].map((key) => (
                                        <div key={key} className="space-y-2">
                                            <p className="section-label">
                                                {key === 'admin' ? (
                                                    <><svg className="w-3.5 h-3.5 inline-block mr-1 -mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg> 관리실</>
                                                ) : key === 'tower' ? (
                                                    <><svg className="w-3.5 h-3.5 inline-block mr-1 -mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" /></svg> 타워</>
                                                ) : (
                                                    <><svg className="w-3.5 h-3.5 inline-block mr-1 -mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg> 대기</>
                                                )} 배정
                                            </p>
                                            <div className="flex flex-wrap gap-2 p-3 bg-surface-muted rounded-input border border-line-light min-h-[50px]">
                                                {data?.users.map(user => {
                                                    const isSelected = (newHistoryForm as any)[key]?.some((item: string) => item.startsWith(user.name));
                                                    return (
                                                        <button
                                                            key={user.name}
                                                            onClick={() => {
                                                                const currentList = [...((newHistoryForm as any)[key] || [])];
                                                                const existsIdx = currentList.findIndex((item: string) => item.startsWith(user.name));
                                                                if (existsIdx > -1) {
                                                                    currentList.splice(existsIdx, 1);
                                                                    setNewHistoryForm({ ...newHistoryForm, [key]: currentList });
                                                                } else {
                                                                    const otherKeys = ['admin', 'tower', 'wait'].filter(k => k !== key);
                                                                    const updated = { ...newHistoryForm } as any;
                                                                    otherKeys.forEach(ok => {
                                                                        updated[ok] = (updated[ok] || []).filter((item: string) => !item.startsWith(user.name));
                                                                    });
                                                                    currentList.push(`${user.name} (${user.car_type}) 수동입력`);
                                                                    setNewHistoryForm({ ...updated, [key]: currentList });
                                                                }
                                                            }}
                                                            className={`px-3 py-1.5 rounded-tag text-[10px] font-bold transition-all border ${isSelected
                                                                ? (key === 'admin' ? 'bg-primary-500 text-white border-primary-600 shadow-md shadow-primary-100' : key === 'tower' ? 'bg-secondary-500 text-white border-secondary-600 shadow-md shadow-secondary-100' : 'bg-ink-secondary text-white border-ink')
                                                                : 'bg-surface-card text-ink-tertiary border-line-light hover:border-line'
                                                                }`}
                                                        >
                                                            {user.name}
                                                        </button>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    ))}

                                    <div className="flex gap-3 pt-2">
                                        <button onClick={handleAddHistory} className="btn-primary flex-1 py-4 text-sm">추가하기</button>
                                        <button
                                            onClick={() => { setIsAddingHistory(false); setNewHistoryForm({ date: '', admin: [], tower: [], wait: [] }); }}
                                            className="flex-1 py-4 bg-surface-muted text-ink-tertiary rounded-button font-bold hover:bg-line-light transition-all"
                                        >
                                            취소
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )}

                        {filteredHistory.map((h) => (
                            <div key={h.date} className="card group">
                                <div className="flex justify-between items-center mb-6">
                                    <div className="flex items-center gap-3">
                                        <span className="text-xl font-black text-ink">{h.date}</span>
                                        <span className="tag-blue text-[10px]">배정완료</span>
                                    </div>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => handleSendSlack(h.date)}
                                            className={`w-10 h-10 flex items-center justify-center rounded-tag transition-all ${h.slack_notified ? 'bg-primary-50 text-primary-500' : 'bg-surface-muted text-ink-placeholder hover:text-primary-500 hover:bg-primary-50'}`}
                                            title="슬랙 알림 전송"
                                        >
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" /></svg>
                                        </button>
                                        <button
                                            onClick={() => {
                                                setEditingHistoryDate(h.date);
                                                setEditHistoryForm(h);
                                            }}
                                            className="w-10 h-10 flex items-center justify-center rounded-tag bg-surface-muted text-ink-placeholder hover:text-primary-500 hover:bg-primary-50 transition-all"
                                        >
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                                        </button>
                                        <button
                                            onClick={() => handleDeleteHistory(h.date)}
                                            className="w-10 h-10 flex items-center justify-center rounded-tag bg-surface-muted text-ink-placeholder hover:text-danger-500 hover:bg-danger-50 transition-all"
                                        >
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                                        </button>
                                    </div>
                                </div>

                                {editingHistoryDate === h.date ? (
                                    <div className="space-y-6 animate-fade-in py-6 bg-surface-muted p-6 rounded-button border border-line-light">
                                        <div className="space-y-4">
                                            {['admin', 'tower', 'wait'].map((key) => (
                                                <div key={key} className="space-y-2">
                                                    <p className="section-label">
                                                        {key === 'admin' ? (
                                                            <><svg className="w-3.5 h-3.5 inline-block mr-1 -mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg> 관리실</>
                                                        ) : key === 'tower' ? (
                                                            <><svg className="w-3.5 h-3.5 inline-block mr-1 -mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" /></svg> 타워</>
                                                        ) : (
                                                            <><svg className="w-3.5 h-3.5 inline-block mr-1 -mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg> 대기</>
                                                        )} 배정
                                                    </p>
                                                    <div className="flex flex-wrap gap-2 p-3 bg-surface-card rounded-input border border-line-light min-h-[50px]">
                                                        {data?.users.map(user => {
                                                            const isSelected = (editHistoryForm as any)[key]?.some((item: string) => item.startsWith(user.name));
                                                            return (
                                                                <button
                                                                    key={user.name}
                                                                    onClick={() => {
                                                                        const currentList = [...((editHistoryForm as any)[key] || [])];
                                                                        const existsIdx = currentList.findIndex((item: string) => item.startsWith(user.name));
                                                                        if (existsIdx > -1) {
                                                                            currentList.splice(existsIdx, 1);
                                                                        } else {
                                                                            const otherKeys = ['admin', 'tower', 'wait'].filter(k => k !== key);
                                                                            const newForm = { ...editHistoryForm } as any;
                                                                            otherKeys.forEach(ok => {
                                                                                newForm[ok] = (newForm[ok] || []).filter((item: string) => !item.startsWith(user.name));
                                                                            });
                                                                            currentList.push(`${user.name} (${user.car_type}) 수동입력`);
                                                                            setEditHistoryForm({ ...newForm, [key]: currentList });
                                                                            return;
                                                                        }
                                                                        setEditHistoryForm({ ...editHistoryForm, [key]: currentList });
                                                                    }}
                                                                    className={`px-3 py-1.5 rounded-tag text-[10px] font-bold transition-all border ${isSelected
                                                                        ? (key === 'admin' ? 'bg-primary-500 text-white border-primary-600 shadow-md shadow-primary-100' : key === 'tower' ? 'bg-secondary-500 text-white border-secondary-600 shadow-md shadow-secondary-100' : 'bg-ink-secondary text-white border-ink')
                                                                        : 'bg-surface-muted text-ink-tertiary border-line-light hover:border-line'
                                                                        }`}
                                                                >
                                                                    {user.name}
                                                                </button>
                                                            );
                                                        })}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>

                                        <div className="flex gap-2 pt-2">
                                            <button onClick={handleUpdateHistory} className="btn-primary flex-1 py-4 text-sm">수정 내역 저장</button>
                                            <button onClick={() => setEditingHistoryDate(null)} className="flex-1 py-4 bg-surface-card text-ink-tertiary rounded-button font-black text-xs border border-line-light shadow-sm">취소</button>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="grid grid-cols-3 gap-3">
                                        <div className="p-4 bg-primary-50/30 rounded-input border border-primary-50">
                                            <span className="section-label text-primary-300 block mb-2">관리실</span>
                                            <div className="space-y-1 font-bold text-sm text-ink">
                                                {h.admin.map(name => <p key={name}>{name.split(' (')[0]}</p>)}
                                                {h.admin.length === 0 && <p className="text-ink-placeholder italic">없음</p>}
                                            </div>
                                        </div>
                                        <div className="p-4 bg-secondary-50/30 rounded-input border border-secondary-50">
                                            <span className="section-label text-secondary-400 block mb-2">타워</span>
                                            <div className="space-y-1 font-bold text-sm text-ink">
                                                {h.tower.map(name => <p key={name}>{name.split(' (')[0]}</p>)}
                                                {h.tower.length === 0 && <p className="text-ink-placeholder italic">없음</p>}
                                            </div>
                                        </div>
                                        <div className="p-4 bg-surface-muted rounded-input border border-line-light">
                                            <span className="section-label text-ink-placeholder block mb-2">대기</span>
                                            <div className="space-y-1 font-bold text-xs text-ink-tertiary">
                                                {h.wait.map(name => <p key={name}>{name.split(' (')[0]}</p>)}
                                                {h.wait.length === 0 && <p className="text-ink-placeholder italic">없음</p>}
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}

                {/* ================================
                    Data Management Tab
                    ================================ */}
                {activeTab === 'data' && (
                    <div className="space-y-8">
                        <div className="card">
                            <h3 className="section-title mb-8">실시간 신청 대기열</h3>
                            <div className="space-y-6">
                                <div className="space-y-3">
                                    <p className="text-xs font-bold text-ink-tertiary ml-1 flex justify-between items-center">
                                        <span>
                                            <svg className="w-3.5 h-3.5 inline-block mr-1 -mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>
                                            리서처 주차 신청 ({data?.requests.applicants.length || 0})
                                        </span>
                                        <span className="tag-blue text-[10px]">자정 마감</span>
                                    </p>
                                    <div className="flex flex-wrap gap-2">
                                        {data?.requests.applicants.map((a: any) => {
                                            const name = typeof a === 'string' ? a : a.name;
                                            const time = typeof a === 'object' && a.timestamp ? new Date(a.timestamp).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }) : '';
                                            return (
                                                <div key={name} className="px-4 py-2 bg-surface-card rounded-input text-sm font-bold text-ink-secondary border border-line-light shadow-sm flex items-center gap-2 group">
                                                    {name}
                                                    {time && <span className="tag-blue text-[9px]">{time}</span>}
                                                    <button
                                                        onClick={async () => {
                                                            if (!confirm(`${name}님의 주차 신청을 취소하시겠습니까?`)) return;
                                                            try {
                                                                const res = await fetch('/api/apply', {
                                                                    method: 'DELETE',
                                                                    headers: { 'Content-Type': 'application/json' },
                                                                    body: JSON.stringify({ name }),
                                                                });
                                                                const result = await res.json();
                                                                if (res.ok) {
                                                                    fetchData();
                                                                } else {
                                                                    alert(result.error || '취소 처리에 실패했습니다.');
                                                                }
                                                            } catch {
                                                                alert('취소 처리 중 오류가 발생했습니다.');
                                                            }
                                                        }}
                                                        className="ml-1 w-5 h-5 flex items-center justify-center rounded-full text-ink-placeholder hover:text-danger-500 hover:bg-danger-50 transition-all opacity-0 group-hover:opacity-100"
                                                        title={`${name} 신청 취소`}
                                                    >
                                                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" /></svg>
                                                    </button>
                                                </div>
                                            );
                                        })}
                                        {data?.requests.applicants.length === 0 && <p className="p-8 w-full text-center text-ink-placeholder italic text-sm">신청 인원이 없습니다.</p>}
                                    </div>
                                </div>

                                <div className="space-y-3 pt-6 border-t border-line-light">
                                    <p className="section-label ml-1">
                                        <svg className="w-3.5 h-3.5 inline-block mr-1 -mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" /></svg>
                                        외부 방문객 신청 ({data?.requests.guests.length || 0})
                                    </p>
                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                        {data?.requests.guests.map((g, i) => (
                                            <div key={i} className="bg-surface-card p-4 rounded-button border border-line-light shadow-sm flex justify-between items-center group">
                                                <div>
                                                    <p className="font-extrabold text-ink">{g.name} <span className="tag-purple text-[10px] ml-1">{g.car_type}</span></p>
                                                    <p className="text-[10px] text-ink-tertiary font-bold mt-1">위치: {g.location.join('/')}</p>
                                                </div>
                                                <button
                                                    onClick={async () => {
                                                        if (!confirm('방문객 신청을 삭제하시겠습니까?')) return;
                                                        await fetch('/api/guests', {
                                                            method: 'DELETE',
                                                            headers: { 'Content-Type': 'application/json' },
                                                            body: JSON.stringify({ index: i }),
                                                        });
                                                        fetchData();
                                                    }}
                                                    className="w-10 h-10 flex items-center justify-center rounded-tag bg-surface-muted text-ink-placeholder hover:text-danger-500 transition-all opacity-0 group-hover:opacity-100"
                                                >
                                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" /></svg>
                                                </button>
                                            </div>
                                        ))}
                                        {data?.requests.guests.length === 0 && <p className="col-span-2 p-8 text-center text-ink-placeholder italic text-sm">신청 방문객이 없습니다.</p>}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="card border-primary-50 bg-primary-50/10">
                            <h3 className="section-label text-primary-500 mb-2">GitHub Connection Diagnostic</h3>
                            <p className="text-[10px] text-ink-tertiary mb-6 font-medium">현재 데이터 저장소(GitHub)와의 연결 상태 및 파일 무결성을 점검합니다.</p>

                            {githubCheckResult && (
                                <div className={`p-6 rounded-button mb-6 border ${githubCheckResult.status === 'success' ? 'bg-success-50 border-success-100 text-success-600' : githubCheckResult.status === 'warning' ? 'bg-warning-50 border-warning-100 text-warning-500' : 'bg-danger-50 border-danger-100 text-danger-500'}`}>
                                    <div className="flex items-center gap-2 mb-4">
                                        <div className={`w-2 h-2 rounded-full animate-pulse ${githubCheckResult.status === 'success' ? 'bg-success-500' : githubCheckResult.status === 'warning' ? 'bg-warning-500' : 'bg-danger-500'}`} />
                                        <span className="text-xs font-black">{githubCheckResult.message}</span>
                                    </div>
                                    <div className="space-y-2">
                                        <div className="grid grid-cols-2 gap-2 text-[10px]">
                                            <div className="p-2 bg-white/50 rounded-tag">
                                                <p className="text-ink-tertiary font-bold mb-1">Authenticated As</p>
                                                <p className="font-extrabold">{githubCheckResult.details?.user || 'Unknown'}</p>
                                            </div>
                                            <div className="p-2 bg-white/50 rounded-tag">
                                                <p className="text-ink-tertiary font-bold mb-1">Target Repo</p>
                                                <p className="font-extrabold">{githubCheckResult.details?.repo || 'Not Found'}</p>
                                            </div>
                                        </div>
                                        {githubCheckResult.details?.files && (
                                            <div className="p-3 bg-white/50 rounded-tag mt-2">
                                                <p className="section-label mb-1">Repo Files Found</p>
                                                <div className="flex flex-wrap gap-1.5">
                                                    {githubCheckResult.details.files.map((f: string) => (
                                                        <span key={f} className="px-1.5 py-0.5 bg-surface-card text-ink-secondary rounded text-[9px] border border-line-light">{f}</span>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}

                            <button
                                onClick={handleCheckGithub}
                                disabled={isCheckingGithub}
                                className={`btn-secondary w-full py-4 rounded-button hover:bg-primary-500 hover:text-white hover:border-primary-500 ${isCheckingGithub ? 'opacity-50 cursor-not-allowed' : ''}`}
                            >
                                {isCheckingGithub ? '진단 중...' : 'GitHub 연결 상태 확인 및 대조'}
                            </button>
                        </div>

                        <div className="card border-danger-50 !bg-danger-50/20">
                            <h3 className="section-label text-danger-500 mb-2">Danger Zone</h3>
                            <p className="text-[10px] text-ink-tertiary mb-6">오늘 들어온 모든 신청 내역(직원, 손님)을 즉시 초기화합니다.</p>
                            <button
                                onClick={handleResetRequests}
                                className="btn-danger"
                            >
                                오늘 신청 내역 전체 초기화
                            </button>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}
