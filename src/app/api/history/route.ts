import { NextRequest, NextResponse } from 'next/server';
import { loadFromGithub, saveToGithub } from '@/lib/github';
import { HistoryEntry, RequestsData } from '@/types';

export async function POST(request: NextRequest) {
    try {
        const { date, admin, tower, wait } = await request.json();
        const { data: history, sha } = await loadFromGithub<HistoryEntry[]>('history.json', []);

        if (history.some((h) => h.date === date))
            return NextResponse.json({ error: `${date} 날짜의 배정이 이미 존재합니다.` }, { status: 409 });

        history.push({ date, admin: admin || [], tower: tower || [], wait: wait || [], slack_notified: false });
        history.sort((a, b) => b.date.localeCompare(a.date));
        await saveToGithub('history.json', history, sha, `수동 배정 추가: ${date}`);

        // 수동 배정 후 requests.json 신청 목록 초기화
        const { data: requests, sha: reqSha } = await loadFromGithub<RequestsData>(
            'requests.json',
            { target_date: '', applicants: [], guests: [], sante_opt_out: false }
        );
        if (requests.applicants?.length || requests.guests?.length) {
            requests.applicants = [];
            requests.guests = [];
            await saveToGithub('requests.json', requests, reqSha, `수동 배정으로 신청 초기화: ${date}`);
        }

        return NextResponse.json({ success: true });
    } catch (e) {
        return NextResponse.json({ error: '처리 중 오류가 발생했습니다.' }, { status: 500 });
    }
}

export async function PUT(request: NextRequest) {
    try {
        const { date, admin, tower, wait } = await request.json();
        const { data: history, sha } = await loadFromGithub<HistoryEntry[]>('history.json', []);

        const idx = history.findIndex((h) => h.date === date);
        if (idx === -1) return NextResponse.json({ error: '해당 날짜를 찾을 수 없습니다.' }, { status: 404 });

        history[idx] = { ...history[idx], admin, tower, wait };
        await saveToGithub('history.json', history, sha, `배정 수정: ${date}`);
        return NextResponse.json({ success: true });
    } catch (e) {
        return NextResponse.json({ error: '처리 중 오류가 발생했습니다.' }, { status: 500 });
    }
}

export async function DELETE(request: NextRequest) {
    try {
        const { date } = await request.json();
        const { data: history, sha } = await loadFromGithub<HistoryEntry[]>('history.json', []);

        const filtered = history.filter((h) => h.date !== date);
        if (filtered.length === history.length)
            return NextResponse.json({ error: '해당 날짜를 찾을 수 없습니다.' }, { status: 404 });

        await saveToGithub('history.json', filtered, sha, `배정 삭제: ${date}`);
        return NextResponse.json({ success: true });
    } catch (e) {
        return NextResponse.json({ error: '처리 중 오류가 발생했습니다.' }, { status: 500 });
    }
}
