import { NextRequest, NextResponse } from 'next/server';
import { loadFromGithub, saveToGithub } from '@/lib/github';
import { RequestsData } from '@/types';

const DEFAULT_REQUESTS: RequestsData = {
    target_date: '',
    applicants: [],
    guests: [],
    sante_opt_out: false,
};

/**
 * POST /api/apply
 * 주차 신청 추가
 * body: { name: string, timestamp: string }
 */
export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const { name, timestamp } = body;

        if (!name) {
            return NextResponse.json({ error: '이름을 입력해주세요.' }, { status: 400 });
        }

        const { data: requests, sha } = await loadFromGithub<RequestsData>('requests.json', DEFAULT_REQUESTS);

        // 중복 신청 방지
        const alreadyApplied = requests.applicants.some((a) => a.name === name);
        if (alreadyApplied) {
            return NextResponse.json({ error: '이미 신청하셨습니다.', alreadyApplied: true }, { status: 409 });
        }

        // 신청 추가
        requests.applicants.push({
            name,
            timestamp: timestamp || new Date().toISOString(),
        });

        const saved = await saveToGithub(
            'requests.json',
            requests,
            sha,
            `주차 신청: ${name} (${new Date().toLocaleDateString('ko-KR')})`
        );

        if (!saved) {
            return NextResponse.json({ error: '신청 저장에 실패했습니다.' }, { status: 500 });
        }

        return NextResponse.json({ success: true, message: `${name}님의 주차 신청이 완료되었습니다.` });
    } catch (error) {
        console.error('[/api/apply] 오류:', error);
        return NextResponse.json({ error: '신청 처리 중 오류가 발생했습니다.' }, { status: 500 });
    }
}

/**
 * DELETE /api/apply
 * 주차 신청 취소
 * body: { name: string }
 */
export async function DELETE(request: NextRequest) {
    try {
        const { name, reset } = await request.json();
        const { data: requests, sha } = await loadFromGithub<RequestsData>('requests.json', DEFAULT_REQUESTS);

        if (reset) {
            requests.applicants = [];
            requests.guests = [];
            await saveToGithub('requests.json', requests, sha, '오늘의 모든 신청 내역 초기화');
            return NextResponse.json({ success: true, message: '모든 신청 내역이 초기화되었습니다.' });
        }

        if (!name) {
            return NextResponse.json({ error: '이름을 입력해주세요.' }, { status: 400 });
        }

        const originalLength = requests.applicants.length;
        requests.applicants = requests.applicants.filter((a) => a.name !== name);

        if (requests.applicants.length === originalLength) {
            return NextResponse.json({ error: '신청 내역을 찾을 수 없습니다.' }, { status: 404 });
        }

        await saveToGithub(
            'requests.json',
            requests,
            sha,
            `주차 신청 취소: ${name} (${new Date().toLocaleDateString('ko-KR')})`
        );

        return NextResponse.json({ success: true, message: `${name}님의 신청이 취소되었습니다.` });
    } catch (error) {
        console.error('[/api/apply DELETE] 오류:', error);
        return NextResponse.json({ error: '취소 처리 중 오류가 발생했습니다.' }, { status: 500 });
    }
}
