'use client';

import { useState, useEffect, useMemo } from 'react';
import { User, RequestsData, HistoryEntry } from '@/types';
import * as XLSX from 'xlsx';

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
                // history item might be "Name (CarType) Time" - need to check if starts with Name
                if (combined.some(item => item.split(' (')[0] === user.name)) {
                    lastDate = h.date;
                    break; // first one found (history is sorted by date desc)
                }
            }
            return { ...user, calculated_last_parked: lastDate };
        });
    }, [data]);

    const handleAllocate = async () => {
        if (!adminKey && !showKeyInput) {
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
        if (!adminKey && !showKeyInput) {
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
        if (!adminKey && !showKeyInput) {
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

    if (loading) return <div className="flex h-screen items-center justify-center font-bold text-blue-500 animate-pulse">관리자 데이터 로드 중...</div>;

    return (
        <div className="mx-auto max-w-4xl min-h-screen pb-20 px-4">
            <header className="py-8 flex justify-between items-center">
                <h2 className="text-3xl font-extrabold tracking-tight">관리자 페이지</h2>
                <button
                    onClick={onBack}
                    className="px-6 py-2 bg-white rounded-full text-xs font-bold text-gray-400 border border-gray-100 shadow-sm hover:text-blue-500 transition-all"
                >
                    메인으로 돌아가기
                </button>
            </header>

            {/* Navigation Tabs */}
            <nav className="flex space-x-2 mb-8 p-1 bg-gray-100 rounded-2xl overflow-x-auto scrollbar-hide">
                {[
                    { id: 'result', label: '배정 결과' },
                    { id: 'users', label: '직원 관리' },
                    { id: 'history', label: '히스토리' },
                    { id: 'data', label: '데이터 관리' },
                ].map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id as any)}
                        className={`flex-1 min-w-[80px] py-2.5 rounded-xl text-xs font-bold transition-all ${activeTab === tab.id
                            ? 'bg-white text-blue-600 shadow-sm'
                            : 'text-gray-400 hover:text-gray-600'
                            }`}
                    >
                        {tab.label}
                    </button>
                ))}
            </nav>

            <main className="animate-fade-in">
                {activeTab === 'result' && (
                    <div className="space-y-6">
                        <div className="card-container">
                            <h3 className="text-xl font-bold mb-6">오늘의 배정 현황</h3>
                            {data?.history[0]?.date === new Date().toISOString().split('T')[0] ? (
                                <div className="space-y-6">
                                    <div className="flex flex-col sm:flex-row gap-2">
                                        <div className="flex-1 p-4 bg-green-50 text-green-600 rounded-2xl font-bold text-center border border-green-100 flex items-center justify-center">
                                            오늘의 배정이 완료되었습니다.
                                        </div>
                                        <button
                                            onClick={() => handleSendSlack(data.history[0].date)}
                                            className="px-6 py-4 bg-white border border-blue-100 text-blue-500 rounded-2xl font-bold text-sm hover:bg-blue-50 transition-all flex items-center justify-center gap-2"
                                        >
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" /></svg>
                                            슬랙 알림 전송 {data.history[0].slack_notified && <span className="text-[10px] bg-blue-100 px-1.5 rounded ml-1">완료</span>}
                                        </button>
                                    </div>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="p-6 bg-blue-50/50 rounded-3xl border border-blue-100">
                                            <p className="text-xs text-blue-500 font-bold mb-2">🏢 관리실</p>
                                            <div className="space-y-1">
                                                {data.history[0].admin.map(name => <p key={name} className="text-lg font-black text-gray-800">{name}</p>)}
                                                {data.history[0].admin.length === 0 && <p className="text-gray-300">배정 없음</p>}
                                            </div>
                                        </div>
                                        <div className="p-6 bg-purple-50/50 rounded-3xl border border-purple-100">
                                            <p className="text-xs text-purple-500 font-bold mb-2">🅿️ 타워</p>
                                            <div className="space-y-1">
                                                {data.history[0].tower.map(name => <p key={name} className="text-lg font-black text-gray-800">{name}</p>)}
                                                {data.history[0].tower.length === 0 && <p className="text-gray-300">배정 없음</p>}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="text-center py-10">
                                    <p className="text-gray-400 font-medium mb-8 text-sm">배정 결과가 아직 생성되지 않았습니다.</p>
                                    {showKeyInput && (
                                        <input
                                            type="password"
                                            placeholder="Admin Key"
                                            value={adminKey}
                                            onChange={(e) => setAdminKey(e.target.value)}
                                            className="w-full mb-4 p-4 rounded-2xl bg-gray-50 border border-gray-100 outline-none focus:ring-2 focus:ring-blue-500 text-center font-bold"
                                        />
                                    )}
                                    <button
                                        onClick={handleAllocate}
                                        className="toss-btn-primary w-full"
                                    >
                                        배정 계산 수동 실행
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {activeTab === 'users' && (
                    <div className="space-y-6">
                        <div className="flex justify-between items-center px-2">
                            <h3 className="text-xl font-bold">직원 리스트 <span className="text-blue-500 text-sm ml-2">{data?.users.length}명</span></h3>
                            <div className="flex gap-2">
                                <button
                                    onClick={downloadStaffExcel}
                                    className="px-4 py-2 bg-green-50 text-green-600 rounded-xl text-[10px] font-bold flex items-center gap-1 border border-green-100"
                                >
                                    📥 엑셀 다운
                                </button>
                                <button
                                    onClick={() => setIsAddingUser(true)}
                                    className="px-4 py-2 bg-blue-600 text-white rounded-xl text-[10px] font-bold shadow-md shadow-blue-200"
                                >
                                    + 직원 추가
                                </button>
                            </div>
                        </div>

                        {(isAddingUser || editingUserIndex !== null) && (
                            <div className="card-container border-2 border-blue-200 animate-fade-in mb-8">
                                <h4 className="font-bold mb-6 text-blue-600">{isAddingUser ? '새 직원 등록' : '직원 정보 수정'}</h4>
                                <div className="space-y-4">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-1">
                                            <label className="text-[10px] font-bold text-gray-400 ml-1">이름</label>
                                            <input
                                                placeholder="이름"
                                                value={isAddingUser ? (newUser.name || '') : (editUserForm.name || '')}
                                                onChange={(e) => isAddingUser ? setNewUser({ ...newUser, name: e.target.value }) : setEditUserForm({ ...editUserForm, name: e.target.value })}
                                                className="w-full p-4 bg-gray-50 rounded-2xl outline-none font-bold text-gray-700"
                                            />
                                        </div>
                                        <div className="space-y-1">
                                            <label className="text-[10px] font-bold text-gray-400 ml-1">차종</label>
                                            <select
                                                value={isAddingUser ? newUser.car_type : editUserForm.car_type}
                                                onChange={(e) => isAddingUser ? setNewUser({ ...newUser, car_type: e.target.value as any }) : setEditUserForm({ ...editUserForm, car_type: e.target.value as any })}
                                                className="w-full p-4 bg-gray-50 rounded-2xl outline-none font-bold text-gray-700"
                                            >
                                                <option value="SEDAN">SEDAN (세단)</option>
                                                <option value="SUV">SUV (대형)</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-1">
                                            <label className="text-[10px] font-bold text-gray-400 ml-1">차 번호</label>
                                            <input
                                                placeholder="예: 12가 3456"
                                                value={isAddingUser ? (newUser.car_number || '') : (editUserForm.car_number || '')}
                                                onChange={(e) => isAddingUser ? setNewUser({ ...newUser, car_number: e.target.value }) : setEditUserForm({ ...editUserForm, car_number: e.target.value })}
                                                className="w-full p-4 bg-gray-50 rounded-2xl outline-none"
                                            />
                                        </div>
                                        <div className="space-y-1">
                                            <label className="text-[10px] font-bold text-gray-400 ml-1">상세 차종</label>
                                            <input
                                                placeholder="예: 아반떼 CN7"
                                                value={isAddingUser ? (newUser.car_details || '') : (editUserForm.car_details || '')}
                                                onChange={(e) => isAddingUser ? setNewUser({ ...newUser, car_details: e.target.value }) : setEditUserForm({ ...editUserForm, car_details: e.target.value })}
                                                className="w-full p-4 bg-gray-50 rounded-2xl outline-none"
                                            />
                                        </div>
                                    </div>
                                    <div className="flex gap-3 pt-4">
                                        <button
                                            onClick={isAddingUser ? handleAddUser : handleEditUser}
                                            className="toss-btn-primary flex-1 py-3"
                                        >
                                            저장하기
                                        </button>
                                        <button
                                            onClick={() => { setIsAddingUser(false); setEditingUserIndex(null); }}
                                            className="flex-1 py-3 bg-gray-100 text-gray-400 rounded-3xl font-bold hover:bg-gray-200 transition-all"
                                        >
                                            취소
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )}

                        <div className="card-container !p-0 overflow-hidden overflow-x-auto scrollbar-hide">
                            <table className="w-full text-left border-collapse">
                                <thead>
                                    <tr className="bg-gray-50/50 border-b border-gray-100">
                                        <th className="px-6 py-4 text-[10px] font-black text-gray-400 uppercase tracking-wider">이름</th>
                                        <th className="px-6 py-4 text-[10px] font-black text-gray-400 uppercase tracking-wider text-center">차종</th>
                                        <th className="px-6 py-4 text-[10px] font-black text-gray-400 uppercase tracking-wider">차 번호</th>
                                        <th className="px-6 py-4 text-[10px] font-black text-gray-400 uppercase tracking-wider">상세 차종</th>
                                        <th className="px-6 py-4 text-[10px] font-black text-gray-400 uppercase tracking-wider">마지막 주차일</th>
                                        <th className="px-6 py-4 text-[10px] font-black text-gray-400 uppercase tracking-wider text-center">관리</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {usersWithLastParked.map((user, idx) => (
                                        <tr key={user.name} className="border-b border-gray-50 last:border-0 hover:bg-gray-50/30 transition-colors">
                                            <td className="px-6 py-4 font-bold text-gray-800 text-sm">{user.name}</td>
                                            <td className="px-6 py-4 text-center">
                                                <span className={`px-2 py-1 rounded-lg text-[9px] font-bold ${user.car_type === 'SUV' ? 'bg-purple-100 text-purple-600' : 'bg-blue-100 text-blue-600'}`}>
                                                    {user.car_type}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-xs text-gray-500 font-medium">{user.car_number || '-'}</td>
                                            <td className="px-6 py-4 text-xs text-gray-500 font-medium">{user.car_details || '-'}</td>
                                            <td className="px-6 py-4 text-xs text-blue-400 font-bold">{user.calculated_last_parked}</td>
                                            <td className="px-6 py-4 whitespace-nowrap text-center">
                                                <div className="flex items-center justify-center gap-2">
                                                    <button
                                                        onClick={() => {
                                                            setEditingUserIndex(idx);
                                                            setEditUserForm(user);
                                                            setIsAddingUser(false);
                                                        }}
                                                        className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-300 hover:text-blue-500 hover:bg-blue-50 transition-all"
                                                    >
                                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                                                    </button>
                                                    <button
                                                        onClick={() => handleDeleteUser(idx)}
                                                        className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-300 hover:text-red-500 hover:bg-red-50 transition-all"
                                                    >
                                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                            {data?.users.length === 0 && <div className="p-20 text-center text-gray-300 font-bold">등록된 직원이 없습니다.</div>}
                        </div>
                    </div>
                )}

                {activeTab === 'history' && (
                    <div className="space-y-6">
                        <div className="flex justify-between items-center px-2">
                            <h3 className="text-xl font-bold">배정 레코드</h3>
                            <div className="flex items-center gap-3">
                                <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-2xl shadow-sm border border-gray-100">
                                    <input
                                        type="date"
                                        className="text-[10px] outline-none font-bold text-gray-500"
                                        onChange={(e) => setHistoryFilter({ ...historyFilter, start: e.target.value })}
                                    />
                                    <span className="text-gray-200">~</span>
                                    <input
                                        type="date"
                                        className="text-[10px] outline-none font-bold text-gray-500"
                                        onChange={(e) => setHistoryFilter({ ...historyFilter, end: e.target.value })}
                                    />
                                </div>
                            </div>
                        </div>

                        {filteredHistory.map((h) => (
                            <div key={h.date} className="card-container group">
                                <div className="flex justify-between items-center mb-6">
                                    <div className="flex items-center gap-3">
                                        <span className="text-xl font-black text-gray-800">{h.date}</span>
                                        <span className="text-[10px] font-bold text-blue-500 bg-blue-50 px-3 py-1 rounded-full">배정완료</span>
                                    </div>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => handleSendSlack(h.date)}
                                            className={`w-10 h-10 flex items-center justify-center rounded-xl transition-all ${h.slack_notified ? 'bg-blue-50 text-blue-500' : 'bg-gray-50 text-gray-300 hover:text-blue-500 hover:bg-blue-50'}`}
                                            title="슬랙 알림 전송"
                                        >
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" /></svg>
                                        </button>
                                        <button
                                            onClick={() => {
                                                setEditingHistoryDate(h.date);
                                                setEditHistoryForm(h);
                                            }}
                                            className="w-10 h-10 flex items-center justify-center rounded-xl bg-gray-50 text-gray-300 hover:text-blue-500 hover:bg-blue-50 transition-all"
                                        >
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                                        </button>
                                        <button
                                            onClick={() => handleDeleteHistory(h.date)}
                                            className="w-10 h-10 flex items-center justify-center rounded-xl bg-gray-50 text-gray-300 hover:text-red-400 hover:bg-red-50 transition-all"
                                        >
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                                        </button>
                                    </div>
                                </div>

                                {editingHistoryDate === h.date ? (
                                    <div className="space-y-6 animate-fade-in py-6 bg-gray-50/50 p-6 rounded-3xl border border-gray-100">
                                        {/* Selection UI for Admin/Tower */}
                                        <div className="space-y-4">
                                            {['admin', 'tower', 'wait'].map((key) => (
                                                <div key={key} className="space-y-2">
                                                    <p className="text-[10px] font-black text-gray-400 ml-1 uppercase">
                                                        {key === 'admin' ? '🏢 관리실' : key === 'tower' ? '🅿️ 타워' : '⏳ 대기'} 배정
                                                    </p>
                                                    <div className="flex flex-wrap gap-2 p-3 bg-white rounded-2xl border border-gray-100 min-h-[50px]">
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
                                                                            // Remove from other lists first
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
                                                                    className={`px-3 py-1.5 rounded-xl text-[10px] font-bold transition-all border ${isSelected
                                                                        ? (key === 'admin' ? 'bg-blue-500 text-white border-blue-600 shadow-md shadow-blue-100' : key === 'tower' ? 'bg-purple-500 text-white border-purple-600 shadow-md shadow-purple-100' : 'bg-gray-500 text-white border-gray-600')
                                                                        : 'bg-gray-50 text-gray-400 border-gray-100 hover:border-gray-300'
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
                                            <button onClick={handleUpdateHistory} className="toss-btn-primary flex-1 py-4 text-sm">수정 내역 저장</button>
                                            <button onClick={() => setEditingHistoryDate(null)} className="flex-1 py-4 bg-white text-gray-400 rounded-[28px] font-black text-xs border border-gray-100 shadow-sm">취소</button>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="grid grid-cols-3 gap-3">
                                        <div className="p-4 bg-blue-50/30 rounded-2xl border border-blue-50">
                                            <span className="text-[9px] font-black text-blue-300 block mb-2 uppercase">관리실</span>
                                            <div className="space-y-1 font-bold text-sm text-gray-700">
                                                {h.admin.map(name => <p key={name}>{name.split(' (')[0]}</p>)}
                                                {h.admin.length === 0 && <p className="text-gray-300 italic">없음</p>}
                                            </div>
                                        </div>
                                        <div className="p-4 bg-purple-50/30 rounded-2xl border border-purple-50">
                                            <span className="text-[9px] font-black text-purple-300 block mb-2 uppercase">타워</span>
                                            <div className="space-y-1 font-bold text-sm text-gray-700">
                                                {h.tower.map(name => <p key={name}>{name.split(' (')[0]}</p>)}
                                                {h.tower.length === 0 && <p className="text-gray-300 italic">없음</p>}
                                            </div>
                                        </div>
                                        <div className="p-4 bg-gray-50/50 rounded-2xl border border-gray-100">
                                            <span className="text-[9px] font-black text-gray-300 block mb-2 uppercase">대기</span>
                                            <div className="space-y-1 font-bold text-xs text-gray-400">
                                                {h.wait.map(name => <p key={name}>{name.split(' (')[0]}</p>)}
                                                {h.wait.length === 0 && <p className="text-gray-200 italic">없음</p>}
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}

                {activeTab === 'data' && (
                    <div className="space-y-8">
                        <div className="card-container">
                            <h3 className="text-xl font-bold mb-8">실시간 신청 대기열</h3>
                            <div className="space-y-6">
                                <div className="space-y-3">
                                    <p className="text-xs font-bold text-gray-400 ml-1 flex justify-between items-center">
                                        <span>🏢 리서처 주차 신청 ({data?.requests.applicants.length || 0})</span>
                                        <span className="text-[10px] text-blue-500 bg-blue-50 px-2 py-0.5 rounded">자정 마감</span>
                                    </p>
                                    <div className="flex flex-wrap gap-2">
                                        {data?.requests.applicants.map((a: any) => {
                                            const name = typeof a === 'string' ? a : a.name;
                                            const time = typeof a === 'object' && a.timestamp ? new Date(a.timestamp).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }) : '';
                                            return (
                                                <div key={name} className="px-4 py-2 bg-white rounded-2xl text-sm font-bold text-gray-600 border border-gray-100 shadow-sm flex items-center gap-2">
                                                    {name}
                                                    {time && <span className="text-[9px] text-blue-300 bg-blue-50 px-1 rounded">{time}</span>}
                                                </div>
                                            );
                                        })}
                                        {data?.requests.applicants.length === 0 && <p className="p-8 w-full text-center text-gray-300 italic text-sm">신청 인원이 없습니다.</p>}
                                    </div>
                                </div>

                                <div className="space-y-3 pt-6 border-t border-gray-50">
                                    <p className="text-xs font-bold text-gray-400 ml-1 uppercase tracking-wider">👤 외부 방문객 신청 ({data?.requests.guests.length || 0})</p>
                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                        {data?.requests.guests.map((g, i) => (
                                            <div key={i} className="bg-white p-4 rounded-[24px] border border-gray-100 shadow-sm flex justify-between items-center group">
                                                <div>
                                                    <p className="font-extrabold text-gray-700">{g.name} <span className="text-[10px] text-blue-400 ml-1">({g.car_type})</span></p>
                                                    <p className="text-[10px] text-gray-400 font-bold mt-1">위치: {g.location.join('/')}</p>
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
                                                    className="w-10 h-10 flex items-center justify-center rounded-xl bg-gray-50 text-gray-300 hover:text-red-500 transition-all opacity-0 group-hover:opacity-100"
                                                >
                                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" /></svg>
                                                </button>
                                            </div>
                                        ))}
                                        {data?.requests.guests.length === 0 && <p className="col-span-2 p-8 text-center text-gray-300 italic text-sm">신청 방문객이 없습니다.</p>}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="card-container border-blue-50 bg-blue-50/10 mb-6">
                            <h3 className="text-sm font-black text-blue-500 mb-2 uppercase tracking-tight">GitHub Connection Diagnostic</h3>
                            <p className="text-[10px] text-gray-400 mb-6 font-medium">현재 데이터 저장소(GitHub)와의 연결 상태 및 파일 무결성을 점검합니다.</p>

                            {githubCheckResult && (
                                <div className={`p-6 rounded-[24px] mb-6 border ${githubCheckResult.status === 'success' ? 'bg-green-50 border-green-100 text-green-700' : githubCheckResult.status === 'warning' ? 'bg-orange-50 border-orange-100 text-orange-700' : 'bg-red-50 border-red-100 text-red-700'}`}>
                                    <div className="flex items-center gap-2 mb-4">
                                        <div className={`w-2 h-2 rounded-full animate-pulse ${githubCheckResult.status === 'success' ? 'bg-green-500' : githubCheckResult.status === 'warning' ? 'bg-orange-500' : 'bg-red-500'}`} />
                                        <span className="text-xs font-black">{githubCheckResult.message}</span>
                                    </div>
                                    <div className="space-y-2">
                                        <div className="grid grid-cols-2 gap-2 text-[10px]">
                                            <div className="p-2 bg-white/50 rounded-lg">
                                                <p className="text-gray-400 font-bold mb-1">Authenticated As</p>
                                                <p className="font-extrabold">{githubCheckResult.details?.user || 'Unknown'}</p>
                                            </div>
                                            <div className="p-2 bg-white/50 rounded-lg">
                                                <p className="text-gray-400 font-bold mb-1">Target Repo</p>
                                                <p className="font-extrabold">{githubCheckResult.details?.repo || 'Not Found'}</p>
                                            </div>
                                        </div>
                                        {githubCheckResult.details?.files && (
                                            <div className="p-3 bg-white/50 rounded-xl mt-2">
                                                <p className="text-[9px] text-gray-400 font-bold mb-1 uppercase">Repo Files Found</p>
                                                <div className="flex flex-wrap gap-1.5">
                                                    {githubCheckResult.details.files.map((f: string) => (
                                                        <span key={f} className="px-1.5 py-0.5 bg-white text-gray-600 rounded text-[9px] border border-gray-100">{f}</span>
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
                                className={`w-full py-4 bg-white border border-blue-100 rounded-3xl font-black text-xs text-blue-500 hover:bg-blue-500 hover:text-white transition-all shadow-sm ${isCheckingGithub ? 'opacity-50 cursor-not-allowed' : ''}`}
                            >
                                {isCheckingGithub ? '진단 중...' : 'GitHub 연결 상태 확인 및 대조'}
                            </button>
                        </div>

                        <div className="card-container border-red-50 !bg-red-50/20">
                            <h3 className="text-sm font-black text-red-500 mb-2 uppercase tracking-tight">Danger Zone</h3>
                            <p className="text-[10px] text-gray-400 mb-6">오늘 들어온 모든 신청 내역(직원, 손님)을 즉시 초기화합니다.</p>
                            <button
                                onClick={handleResetRequests}
                                className="w-full py-4 text-red-500 bg-white border border-red-100 rounded-3xl font-black text-xs hover:bg-red-500 hover:text-white transition-all shadow-sm"
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
