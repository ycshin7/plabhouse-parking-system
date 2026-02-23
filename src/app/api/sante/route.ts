import { NextRequest, NextResponse } from 'next/server';
import { loadFromGithub, saveToGithub } from '@/lib/github';
import { RequestsData } from '@/types';

const DEFAULT: RequestsData = { target_date: '', applicants: [], guests: [], sante_opt_out: false };

export async function POST(request: NextRequest) {
    try {
        const { sante_opt_out } = await request.json();
        const { data, sha } = await loadFromGithub<RequestsData>('requests.json', DEFAULT);
        data.sante_opt_out = sante_opt_out;
        (data as any).sante_status_updated_at = new Date().toISOString();
        await saveToGithub('requests.json', data, sha, `상떼 주차 상태 변경: ${sante_opt_out ? '안함' : '함'}`);
        return NextResponse.json({ success: true });
    } catch (e) {
        return NextResponse.json({ error: '처리 중 오류가 발생했습니다.' }, { status: 500 });
    }
}
