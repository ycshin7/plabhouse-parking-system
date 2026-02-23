import { NextResponse } from 'next/server';
import { loadFromGithub } from '@/lib/github';
import { User, RequestsData, HistoryEntry } from '@/types';

const DEFAULT_REQUESTS: RequestsData = {
    target_date: '',
    applicants: [],
    guests: [],
    sante_opt_out: false,
};

/**
 * GET /api/data
 * users, requests, history 데이터를 한번에 반환
 */
export async function GET() {
    try {
        const [usersResult, requestsResult, historyResult] = await Promise.all([
            loadFromGithub<User[]>('users.json', []),
            loadFromGithub<RequestsData>('requests.json', DEFAULT_REQUESTS),
            loadFromGithub<HistoryEntry[]>('history.json', []),
        ]);

        return NextResponse.json({
            users: usersResult.data,
            requests: requestsResult.data,
            history: historyResult.data,
        });
    } catch (error) {
        console.error('[/api/data] 오류:', error);
        return NextResponse.json({ error: '데이터를 불러오지 못했습니다.' }, { status: 500 });
    }
}
