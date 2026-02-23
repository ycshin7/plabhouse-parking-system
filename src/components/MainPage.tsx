'use client';

import { useState, useEffect, useCallback } from 'react';
import { User, RequestsData, HistoryEntry } from '@/types';

interface MainPageProps {
    onAdmin: () => void;
}

function getKST() {
    const now = new Date();
    const utc = now.getTime() + (now.getTimezoneOffset() * 60000);
    const kstOffset = 9 * 60 * 60 * 1000;
    return new Date(utc + kstOffset);
}

function formatDate(date: Date) {
    return date.toISOString().split('T')[0];
}

function getTargetDate() {
    const now = getKST();
    let target = new Date(now);
    target.setDate(target.getDate() + 1);
    // Skip weekends: Sat -> Mon, Sun -> Mon
    if (target.getDay() === 6) target.setDate(target.getDate() + 2);
    else if (target.getDay() === 0) target.setDate(target.getDate() + 1);
    return formatDate(target);
}

export default function MainPage({ onAdmin }: MainPageProps) {
    const [data, setData] = useState<{ users: User[]; requests: RequestsData; history: HistoryEntry[] } | null>(null);
    const [loading, setLoading] = useState(true);
    const [visitorCount, setVisitorCount] = useState<number>(0);
    const [activeTab, setActiveTab] = useState<'apply' | 'status'>('apply');
    const [selectedUser, setSelectedUser] = useState('');
    const [guestForm, setGuestForm] = useState({ name: '', car_type: 'SEDAN' as 'SEDAN' | 'SUV', location: '상관없음', researcher: '' });

    // UI state for toggling forms
    const [activeForm, setActiveForm] = useState<'none' | 'staff' | 'guest'>('none');

    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    const targetDate = getTargetDate();
    const now = getKST();
    const dayNames = ['일', '월', '화', '수', '목', '금', '토'];
    const targetDay = dayNames[new Date(targetDate).getDay()];

    const fetchData = useCallback(async () => {
        try {
            const res = await fetch('/api/data', { cache: 'no-store' });
            const json = await res.json();
            setData(json);
        } catch (e) {
            console.error('Data fetch error:', e);
        } finally {
            setLoading(false);
        }
    }, []);

    const handleVisitor = useCallback(async () => {
        const hasCounted = sessionStorage.getItem('parking_counted');
        if (!hasCounted) {
            try {
                const res = await fetch('/api/visitor', { method: 'POST' });
                const json = await res.json();
                setVisitorCount(json.count);
                sessionStorage.setItem('parking_counted', 'true');
            } catch (e) {
                const res = await fetch('/api/visitor');
                const json = await res.json();
                setVisitorCount(json.count);
            }
        } else {
            const res = await fetch('/api/visitor');
            const json = await res.json();
            setVisitorCount(json.count);
        }
    }, []);

    useEffect(() => {
        fetchData();
        handleVisitor();
        const timer = setInterval(fetchData, 30000);
        return () => clearInterval(timer);
    }, [fetchData, handleVisitor]);

    const handleApply = async () => {
        if (!selectedUser) return;
        setMessage(null);
        try {
            const res = await fetch('/api/apply', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: selectedUser, timestamp: new Date().toISOString() }),
            });
            if (res.ok) {
                setMessage({ type: 'success', text: `${selectedUser}님 주차 신청 완료!` });
                setSelectedUser('');
                setActiveForm('none'); // Close form on success
                fetchData();
            } else {
                const json = await res.json();
                setMessage({ type: 'error', text: json.error || '신청 중 오류가 발생했습니다.' });
            }
        } catch (e) {
            setMessage({ type: 'error', text: '네트워크 오류가 발생했습니다.' });
        }
    };

    const handleGuestApply = async () => {
        if (!guestForm.name) return;
        setMessage(null);
        try {
            const res = await fetch('/api/guests', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: guestForm.name,
                    car_type: guestForm.car_type,
                    location: [guestForm.location],
                    researcher: guestForm.researcher
                }),
            });
            if (res.ok) {
                setMessage({ type: 'success', text: `${guestForm.name} 방문 주차 신청 완료!` });
                setGuestForm({ name: '', car_type: 'SEDAN', location: '상관없음', researcher: '' });
                setActiveForm('none'); // Close form on success
                fetchData();
            } else {
                const json = await res.json();
                setMessage({ type: 'error', text: json.error || '신청 중 오류가 발생했습니다.' });
            }
        } catch (e) {
            setMessage({ type: 'error', text: '네트워크 오류가 발생했습니다.' });
        }
    };

    const handleSanteToggle = async () => {
        if (!data) return;
        const newStatus = !data.requests.sante_opt_out;
        try {
            const res = await fetch('/api/sante', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sante_opt_out: newStatus }),
            });
            if (res.ok) fetchData();
            else alert('상태 변경 실패');
        } catch (e) {
            console.error('Sante toggle error:', e);
        }
    };

    if (loading) return (
        <div className="flex h-screen items-center justify-center font-bold text-blue-500 animate-pulse bg-white">
            플랩하우스 주차 시스템 로딩 중...
        </div>
    );

    const appliedNames = data?.requests.applicants.map((a: any) => typeof a === 'string' ? a : a.name) || [];
    const todayResult = data?.history.find(h => h.date === formatDate(now));

    return (
        <div className="mx-auto max-w-4xl min-h-screen px-4 pb-20">
            {/* Toolbar Area */}
            <div className="flex justify-between items-center pt-6 pb-2">
                <button
                    onClick={onAdmin}
                    className="px-4 py-2 bg-white/80 rounded-xl text-xs font-bold text-blue-500 border border-blue-100 shadow-sm hover:bg-blue-50 transition-all focus:outline-none"
                >
                    ⚙️ 관리화면 접속
                </button>
                <div className="px-4 py-2 bg-white/50 backdrop-blur-sm rounded-xl text-xs font-bold text-gray-500 border border-gray-100">
                    총 방문자: <span className="text-gray-800">{visitorCount.toLocaleString()}</span>
                </div>
            </div>

            {/* Header */}
            <header className="py-10 text-center animate-fade-in">
                <h1 className="text-[40px] font-black mb-1 leading-tight tracking-tight text-blue-600">플랩하우스 주차 시스템</h1>
                <p className="text-gray-400 font-bold text-lg">{targetDate} ({targetDay}) 배정 신청</p>
            </header>

            {/* Navigation Tabs (Big Buttons Style) */}
            <nav className="flex space-x-2 mb-8 p-1.5 bg-gray-100/50 rounded-2xl border border-gray-100">
                <button
                    onClick={() => setActiveTab('apply')}
                    className={`flex-1 py-3.5 rounded-xl text-sm font-black transition-all ${activeTab === 'apply' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-400 hover:text-gray-600'}`}
                >
                    주차 신청하기
                </button>
                <button
                    onClick={() => setActiveTab('status')}
                    className={`flex-1 py-3.5 rounded-xl text-sm font-black transition-all ${activeTab === 'status' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-400 hover:text-gray-600'}`}
                >
                    배정 현황 (Status)
                </button>
            </nav>

            <main className="animate-fade-in">
                {activeTab === 'apply' && (
                    <div className="space-y-6">
                        {/* Interactive Main Buttons (The 3 Main Items) */}
                        <div className="grid grid-cols-3 gap-3">
                            {/* Staff Toggle Button */}
                            <button
                                onClick={() => setActiveForm(activeForm === 'staff' ? 'none' : 'staff')}
                                className={`group p-5 rounded-[32px] border text-center shadow-sm transition-all transform active:scale-95 ${activeForm === 'staff' ? 'bg-blue-600 border-blue-600 text-white' : 'bg-white border-gray-100 hover:border-blue-200'}`}
                            >
                                <p className={`text-[10px] uppercase font-black mb-1 ${activeForm === 'staff' ? 'text-blue-100' : 'text-gray-400'}`}>리서처</p>
                                <p className="text-xl font-black">{appliedNames.length}명</p>
                            </button>

                            {/* Guest Toggle Button */}
                            <button
                                onClick={() => setActiveForm(activeForm === 'guest' ? 'none' : 'guest')}
                                className={`group p-5 rounded-[32px] border text-center shadow-sm transition-all transform active:scale-95 ${activeForm === 'guest' ? 'bg-purple-600 border-purple-600 text-white' : 'bg-white border-gray-100 hover:border-purple-200'}`}
                            >
                                <p className={`text-[10px] uppercase font-black mb-1 ${activeForm === 'guest' ? 'text-purple-100' : 'text-gray-400'}`}>손님</p>
                                <p className="text-xl font-black">{data?.requests.guests.length}명</p>
                            </button>

                            {/* Sante Toggle Button */}
                            <button
                                onClick={handleSanteToggle}
                                className={`p-5 rounded-[32px] border text-center shadow-sm transition-all transform active:scale-95 ${!data?.requests.sante_opt_out ? 'bg-green-500 border-green-500 text-white' : 'bg-gray-50 border-gray-100 text-gray-400'}`}
                            >
                                <p className={`text-[10px] uppercase font-black mb-1 ${!data?.requests.sante_opt_out ? 'text-green-100' : 'text-gray-400'}`}>상떼주차</p>
                                <p className="text-xl font-black">{!data?.requests.sante_opt_out ? '함' : '안함'}</p>
                            </button>
                        </div>

                        {/* Apply Forms (Conditional Rendering) */}
                        <div className="animate-slide-up">
                            {activeForm === 'staff' && (
                                <div className="bg-white p-8 rounded-[40px] border border-gray-100 shadow-sm animate-fade-in mb-4">
                                    <h3 className="text-xl font-black mb-6 flex items-center gap-2 text-blue-600">
                                        🏎️ 직원 주차 신청
                                    </h3>
                                    <select
                                        value={selectedUser}
                                        onChange={(e) => setSelectedUser(e.target.value)}
                                        className="w-full p-4 rounded-2xl bg-gray-50 border border-gray-100 outline-none font-bold text-gray-700 mb-4 focus:ring-2 focus:ring-blue-500"
                                    >
                                        <option value="">이름을 선택하세요 (자정 마감)</option>
                                        {data?.users.map((u) => (
                                            <option key={u.name} value={u.name} disabled={appliedNames.includes(u.name)}>
                                                {u.name} ({u.car_type}){appliedNames.includes(u.name) ? ' - 신청완료' : ''}
                                            </option>
                                        ))}
                                    </select>
                                    <button
                                        onClick={handleApply}
                                        disabled={!selectedUser}
                                        className="toss-btn-primary w-full py-5 text-lg"
                                    >
                                        지금 신청하기
                                    </button>
                                </div>
                            )}

                            {activeForm === 'guest' && (
                                <div className="bg-white p-8 rounded-[40px] border border-gray-100 shadow-sm animate-fade-in mb-4">
                                    <h3 className="text-xl font-black mb-6 text-purple-600">👤 외부인 주차 신청</h3>
                                    <div className="space-y-4">
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="space-y-1">
                                                <label className="text-[10px] font-black text-gray-400 ml-1 uppercase">방문자 성함/업체명</label>
                                                <input
                                                    type="text"
                                                    value={guestForm.name}
                                                    onChange={(e) => setGuestForm({ ...guestForm, name: e.target.value })}
                                                    className="w-full p-4 bg-gray-50 rounded-2xl border border-gray-100 outline-none font-bold focus:ring-2 focus:ring-purple-500"
                                                    placeholder="성함 입력"
                                                />
                                            </div>
                                            <div className="space-y-1">
                                                <label className="text-[10px] font-black text-gray-400 ml-1 uppercase">담당 연구원</label>
                                                <select
                                                    value={guestForm.researcher}
                                                    onChange={(e) => setGuestForm({ ...guestForm, researcher: e.target.value })}
                                                    className="w-full p-4 bg-gray-50 rounded-2xl border border-gray-100 outline-none font-bold focus:ring-2 focus:ring-purple-500"
                                                >
                                                    <option value="">담당자 선택</option>
                                                    {data?.users.map(u => <option key={u.name} value={u.name}>{u.name}</option>)}
                                                </select>
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="space-y-1">
                                                <label className="text-[10px] font-black text-gray-400 ml-1 uppercase">차종</label>
                                                <select
                                                    value={guestForm.car_type}
                                                    onChange={(e) => setGuestForm({ ...guestForm, car_type: e.target.value as any })}
                                                    className="w-full p-4 bg-gray-50 rounded-2xl border border-gray-100 outline-none font-bold"
                                                >
                                                    <option value="SEDAN">SEDAN (승용)</option>
                                                    <option value="SUV">SUV/Large (대형)</option>
                                                </select>
                                            </div>
                                            <div className="space-y-1">
                                                <label className="text-[10px] font-black text-gray-400 ml-1 uppercase">희망 위치</label>
                                                <select
                                                    value={guestForm.location}
                                                    onChange={(e) => setGuestForm({ ...guestForm, location: e.target.value })}
                                                    className="w-full p-4 bg-gray-50 rounded-2xl border border-gray-100 outline-none font-bold"
                                                >
                                                    <option value="상관없음">상관없음</option>
                                                    <option value="관리실">지상 (관리실)</option>
                                                    <option value="타워">기계식 (타워)</option>
                                                </select>
                                            </div>
                                        </div>
                                        <button
                                            onClick={handleGuestApply}
                                            disabled={!guestForm.name || !guestForm.researcher}
                                            className="w-full py-5 bg-purple-600 text-white rounded-3xl font-black text-lg shadow-lg shadow-purple-100 hover:bg-purple-700 transition-all active:scale-[0.98] disabled:opacity-30"
                                        >
                                            방문 주차 신청하기
                                        </button>
                                    </div>
                                </div>
                            )}

                            {message && activeForm === 'none' && (
                                <div className={`mt-4 p-5 rounded-[32px] text-sm font-bold text-center border animate-fade-in ${message.type === 'success' ? 'bg-green-50 text-green-600 border-green-100' : 'bg-red-50 text-red-600 border-red-100'
                                    }`}>
                                    {message.text}
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {activeTab === 'status' && (
                    <div className="space-y-6 animate-fade-in">
                        {todayResult ? (
                            <div className="bg-white p-8 rounded-[40px] border border-blue-100 shadow-sm bg-blue-50/10">
                                <h3 className="text-xl font-black mb-6 text-blue-800 flex items-center gap-2">
                                    📅 {formatDate(now)} 배정 결과
                                </h3>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                    <div className="p-6 bg-white rounded-3xl border border-blue-50 shadow-sm">
                                        <p className="text-[10px] font-black text-blue-400 uppercase mb-3 px-1 tracking-tighter">🏢 관리실 (지상)</p>
                                        <div className="flex flex-wrap gap-2">
                                            {todayResult.admin.map(name => <span key={name} className="px-3 py-1 bg-blue-50 text-blue-600 rounded-lg font-bold text-sm shadow-sm border border-blue-100">{name.split(' (')[0]}</span>)}
                                            {todayResult.admin.length === 0 && <span className="text-gray-300 italic">배정 없음</span>}
                                        </div>
                                    </div>
                                    <div className="p-6 bg-white rounded-3xl border border-purple-50 shadow-sm">
                                        <p className="text-[10px] font-black text-purple-400 uppercase mb-3 px-1 tracking-tighter">🅿️ 타워 (기계식)</p>
                                        <div className="flex flex-wrap gap-2">
                                            {todayResult.tower.map(name => <span key={name} className="px-3 py-1 bg-purple-50 text-purple-600 rounded-lg font-bold text-sm shadow-sm border border-purple-100">{name.split(' (')[0]}</span>)}
                                            {todayResult.tower.length === 0 && <span className="text-gray-300 italic">배정 없음</span>}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="bg-white p-12 rounded-[40px] border border-gray-100 shadow-sm text-center">
                                <p className="text-gray-400 font-bold mb-1">아직 오늘의 배정 결과가 발표되지 않았습니다.</p>
                                <p className="text-[10px] text-gray-300">매일 00:01에 자동으로 배정이 진행됩니다.</p>
                            </div>
                        )}

                        <div className="bg-white p-8 rounded-[40px] border border-gray-100 shadow-sm">
                            <h4 className="text-sm font-black mb-6 text-gray-400 uppercase tracking-widest px-1 text-center">현재 신청 대기 (내일 배정용)</h4>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="p-6 bg-gray-50/50 rounded-3xl border border-gray-100 flex flex-col items-center justify-center">
                                    <p className="text-[10px] font-black text-gray-400 uppercase mb-2">리서처</p>
                                    <p className="text-3xl font-black text-gray-800 tracking-tighter">
                                        {appliedNames.length}
                                        <span className="text-sm ml-1 text-gray-400 font-bold uppercase">명</span>
                                    </p>
                                </div>
                                <div className="p-6 bg-purple-50/30 rounded-3xl border border-purple-50 flex flex-col items-center justify-center">
                                    <p className="text-[10px] font-black text-purple-400 uppercase mb-2">외부 방문객</p>
                                    <p className="text-3xl font-black text-purple-600 tracking-tighter">
                                        {data?.requests.guests.length || 0}
                                        <span className="text-sm ml-1 text-purple-400 font-bold uppercase">명</span>
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}
