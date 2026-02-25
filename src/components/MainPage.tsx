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
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
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

/** 평일 00:00~00:05 KST 사이 신청 차단 여부 (클라이언트용) */
function isApplicationClosed(): { closed: boolean; message: string } {
    const kst = getKST();
    const day = kst.getDay();
    const hour = kst.getHours();
    const minute = kst.getMinutes();

    if (day === 0 || day === 6) return { closed: false, message: '' };

    if (hour === 0 && minute < 5) {
        return { closed: true, message: '자정 마감 후 배정 처리 중입니다. 00:05 이후 다시 신청해주세요.' };
    }

    return { closed: false, message: '' };
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
    const cutoff = isApplicationClosed();

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
                setActiveForm('none');
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
                setActiveForm('none');
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
            if (res.ok) {
                setMessage({ type: 'success', text: `상떼주차 ${newStatus ? '안함' : '함'}으로 변경되었습니다.` });
                fetchData();
            } else {
                const json = await res.json();
                setMessage({ type: 'error', text: json.error || '상태 변경 실패' });
            }
        } catch (e) {
            setMessage({ type: 'error', text: '네트워크 오류가 발생했습니다.' });
        }
    };

    if (loading) return (
        <div className="flex h-screen items-center justify-center font-bold text-primary-500 animate-pulse bg-white">
            플랩하우스 주차 시스템 로딩 중...
        </div>
    );

    const appliedNames = data?.requests.applicants.map((a: any) => typeof a === 'string' ? a : a.name) || [];
    const todayResult = data?.history.find(h => h.date === formatDate(now));

    return (
        <div className="mx-auto max-w-4xl min-h-screen px-4 pb-20">
            {/* Toolbar */}
            <div className="flex justify-between items-center pt-6 pb-2">
                <button
                    onClick={onAdmin}
                    className="px-4 py-2 bg-white/80 rounded-input text-xs font-bold text-primary-500 border border-primary-100 shadow-sm hover:bg-primary-50 transition-all focus:outline-none"
                >
                    <svg className="w-3.5 h-3.5 inline-block mr-1 -mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                    관리화면
                </button>
                <div className="px-4 py-2 bg-white/50 backdrop-blur-sm rounded-input text-xs font-bold text-ink-tertiary border border-line-light">
                    방문자 <span className="text-ink">{visitorCount.toLocaleString()}</span>
                </div>
            </div>

            {/* Header */}
            <header className="py-10 text-center animate-fade-in">
                <h1 className="text-[40px] font-black mb-1 leading-tight tracking-tight">플랩하우스 주차 시스템</h1>
                <p className="text-ink-tertiary font-bold text-lg">{targetDate} ({targetDay}) 배정 신청</p>
            </header>

            {/* Tab Navigation */}
            <nav className="tab-nav">
                <button
                    onClick={() => setActiveTab('apply')}
                    className={activeTab === 'apply' ? 'tab-btn-active' : 'tab-btn-inactive'}
                >
                    주차 신청하기
                </button>
                <button
                    onClick={() => setActiveTab('status')}
                    className={activeTab === 'status' ? 'tab-btn-active' : 'tab-btn-inactive'}
                >
                    배정 현황
                </button>
            </nav>

            <main className="animate-fade-in">
                {activeTab === 'apply' && cutoff.closed && (
                    <div className="alert-error mb-4 text-center font-bold">
                        {cutoff.message}
                    </div>
                )}

                {activeTab === 'apply' && (
                    <div className="space-y-6">
                        {/* 3 Action Cards */}
                        <div className="grid grid-cols-3 gap-3">
                            {/* Staff Toggle */}
                            <button
                                onClick={() => setActiveForm(activeForm === 'staff' ? 'none' : 'staff')}
                                className={`action-card ${activeForm === 'staff' ? 'bg-primary-500 border-primary-500 text-white' : 'hover:border-primary-200'}`}
                            >
                                <p className={`action-card-label ${activeForm === 'staff' ? 'text-primary-100' : 'text-ink-tertiary'}`}>리서처</p>
                                <p className="action-card-value">{appliedNames.length}명</p>
                            </button>

                            {/* Guest Toggle */}
                            <button
                                onClick={() => setActiveForm(activeForm === 'guest' ? 'none' : 'guest')}
                                className={`action-card ${activeForm === 'guest' ? 'bg-secondary-600 border-secondary-600 text-white' : 'hover:border-secondary-200'}`}
                            >
                                <p className={`action-card-label ${activeForm === 'guest' ? 'text-secondary-100' : 'text-ink-tertiary'}`}>손님</p>
                                <p className="action-card-value">{data?.requests.guests.length}명</p>
                            </button>

                            {/* Sante Toggle */}
                            <button
                                onClick={handleSanteToggle}
                                className={`action-card ${!data?.requests.sante_opt_out ? 'bg-success-500 border-success-500 text-white' : 'text-ink-disabled'}`}
                            >
                                <p className={`action-card-label ${!data?.requests.sante_opt_out ? 'text-success-100' : 'text-ink-tertiary'}`}>상떼주차</p>
                                <p className="action-card-value">{!data?.requests.sante_opt_out ? '함' : '안함'}</p>
                            </button>
                        </div>

                        {/* Apply Forms */}
                        <div className="animate-slide-up">
                            {activeForm === 'staff' && (
                                <div className="card animate-fade-in mb-4 !p-8 !rounded-[40px]">
                                    <h3 className="section-title mb-6 flex items-center gap-2 text-primary-500">
                                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
                                        직원 주차 신청
                                    </h3>
                                    <select
                                        value={selectedUser}
                                        onChange={(e) => setSelectedUser(e.target.value)}
                                        className="input mb-4"
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
                                        disabled={!selectedUser || cutoff.closed}
                                        className="btn-primary w-full py-5 text-lg"
                                    >
                                        {cutoff.closed ? '배정 처리 중' : '지금 신청하기'}
                                    </button>
                                </div>
                            )}

                            {activeForm === 'guest' && (
                                <div className="card animate-fade-in mb-4 !p-8 !rounded-[40px]">
                                    <h3 className="section-title mb-6 text-secondary-600">
                                        <svg className="w-6 h-6 inline-block mr-2 -mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" /></svg>
                                        외부인 주차 신청
                                    </h3>
                                    <div className="space-y-4">
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="space-y-1">
                                                <label className="input-label">방문자 성함/업체명</label>
                                                <input
                                                    type="text"
                                                    value={guestForm.name}
                                                    onChange={(e) => setGuestForm({ ...guestForm, name: e.target.value })}
                                                    className="input focus:ring-secondary-500"
                                                    placeholder="성함 입력"
                                                />
                                            </div>
                                            <div className="space-y-1">
                                                <label className="input-label">담당 연구원</label>
                                                <select
                                                    value={guestForm.researcher}
                                                    onChange={(e) => setGuestForm({ ...guestForm, researcher: e.target.value })}
                                                    className="select focus:ring-secondary-500"
                                                >
                                                    <option value="">담당자 선택</option>
                                                    {data?.users.map(u => <option key={u.name} value={u.name}>{u.name}</option>)}
                                                </select>
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="space-y-1">
                                                <label className="input-label">차종</label>
                                                <select
                                                    value={guestForm.car_type}
                                                    onChange={(e) => setGuestForm({ ...guestForm, car_type: e.target.value as any })}
                                                    className="select"
                                                >
                                                    <option value="SEDAN">SEDAN (승용)</option>
                                                    <option value="SUV">SUV/Large (대형)</option>
                                                </select>
                                            </div>
                                            <div className="space-y-1">
                                                <label className="input-label">희망 위치</label>
                                                <select
                                                    value={guestForm.location}
                                                    onChange={(e) => setGuestForm({ ...guestForm, location: e.target.value })}
                                                    className="select"
                                                >
                                                    <option value="상관없음">상관없음</option>
                                                    <option value="관리실">지상 (관리실)</option>
                                                    <option value="타워">기계식 (타워)</option>
                                                </select>
                                            </div>
                                        </div>
                                        <button
                                            onClick={handleGuestApply}
                                            disabled={!guestForm.name || !guestForm.researcher || cutoff.closed}
                                            className="w-full py-5 bg-secondary-600 text-white rounded-button font-black text-lg shadow-lg shadow-secondary-100 hover:bg-secondary-700 transition-all active:scale-[0.98] disabled:opacity-30 disabled:cursor-not-allowed"
                                        >
                                            {cutoff.closed ? '배정 처리 중' : '방문 주차 신청하기'}
                                        </button>
                                    </div>
                                </div>
                            )}

                            {message && (
                                <div className={message.type === 'success' ? 'alert-success mt-4' : 'alert-error mt-4'}>
                                    {message.text}
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {activeTab === 'status' && (
                    <div className="space-y-6 animate-fade-in">
                        {todayResult ? (
                            <div className="card !rounded-[40px] !p-8 border-primary-100 bg-primary-50/10">
                                <h3 className="section-title mb-6 text-primary-800 flex items-center gap-2">
                                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                                    {formatDate(now)} 배정 결과
                                </h3>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                    <div className="p-6 bg-white rounded-button border border-primary-50 shadow-sm">
                                        <p className="section-label text-primary-400 mb-3 px-1">
                                            <svg className="w-3.5 h-3.5 inline-block mr-1 -mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>
                                            관리실 (지상)
                                        </p>
                                        <div className="flex flex-wrap gap-2">
                                            {todayResult.admin.map(name => <span key={name} className="tag-blue shadow-sm">{name.split(' (')[0]}</span>)}
                                            {todayResult.admin.length === 0 && <span className="text-ink-placeholder italic">배정 없음</span>}
                                        </div>
                                    </div>
                                    <div className="p-6 bg-white rounded-button border border-secondary-50 shadow-sm">
                                        <p className="section-label text-secondary-400 mb-3 px-1">
                                            <svg className="w-3.5 h-3.5 inline-block mr-1 -mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" /></svg>
                                            타워 (기계식)
                                        </p>
                                        <div className="flex flex-wrap gap-2">
                                            {todayResult.tower.map(name => <span key={name} className="tag-purple shadow-sm">{name.split(' (')[0]}</span>)}
                                            {todayResult.tower.length === 0 && <span className="text-ink-placeholder italic">배정 없음</span>}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="card !rounded-[40px] !p-12 text-center">
                                <svg className="w-12 h-12 mx-auto mb-4 text-ink-placeholder" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                                <p className="text-ink-tertiary font-bold mb-1">아직 오늘의 배정 결과가 발표되지 않았습니다.</p>
                                <p className="text-[10px] text-ink-placeholder">매일 00:01에 자동으로 배정이 진행됩니다.</p>
                            </div>
                        )}

                        <div className="card !rounded-[40px] !p-8">
                            <h4 className="section-label text-center mb-6 tracking-widest">현재 신청 대기 (내일 배정용)</h4>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="p-6 bg-surface-muted rounded-button border border-line-light flex flex-col items-center justify-center">
                                    <p className="section-label text-primary-400 mb-2">리서처</p>
                                    <p className="text-3xl font-black text-ink tracking-tighter">
                                        {appliedNames.length}
                                        <span className="text-sm ml-1 text-ink-tertiary font-bold">명</span>
                                    </p>
                                </div>
                                <div className="p-6 bg-secondary-50/30 rounded-button border border-secondary-50 flex flex-col items-center justify-center">
                                    <p className="section-label text-secondary-400 mb-2">외부 방문객</p>
                                    <p className="text-3xl font-black text-secondary-600 tracking-tighter">
                                        {data?.requests.guests.length || 0}
                                        <span className="text-sm ml-1 text-secondary-400 font-bold">명</span>
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
