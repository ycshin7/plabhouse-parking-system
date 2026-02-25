import { NextRequest, NextResponse } from 'next/server';
import { loadFromGithub, saveToGithub } from '@/lib/github';
import { RequestsData, Guest } from '@/types';

const DEFAULT: RequestsData = { target_date: '', applicants: [], guests: [], sante_opt_out: false };

export async function POST(request: NextRequest) {
    try {
        const body: Guest & { researcher?: string } = await request.json();
        if (!body.name) return NextResponse.json({ error: '방문자 이름을 입력해주세요.' }, { status: 400 });

        const { data, sha } = await loadFromGithub<RequestsData>('requests.json', DEFAULT);
        if (!data.guests) data.guests = [];

        data.guests.push({
            name: body.researcher ? `${body.name} (${body.researcher})` : body.name,
            car_type: body.car_type || 'SEDAN',
            location: body.location || ['상관없음'],
            timestamp: new Date().toISOString(),
        });

        const saved = await saveToGithub('requests.json', data, sha, `외부인 신청: ${body.name}`);
        if (!saved) {
            return NextResponse.json({ error: '신청 저장에 실패했습니다.' }, { status: 500 });
        }
        return NextResponse.json({ success: true });
    } catch (e) {
        return NextResponse.json({ error: '처리 중 오류가 발생했습니다.' }, { status: 500 });
    }
}

export async function DELETE(request: NextRequest) {
    try {
        const { index } = await request.json();
        const { data, sha } = await loadFromGithub<RequestsData>('requests.json', DEFAULT);
        if (!data.guests || index < 0 || index >= data.guests.length)
            return NextResponse.json({ error: '잘못된 요청입니다.' }, { status: 400 });

        data.guests.splice(index, 1);
        await saveToGithub('requests.json', data, sha, `외부인 신청 취소`);
        return NextResponse.json({ success: true });
    } catch (e) {
        return NextResponse.json({ error: '처리 중 오류가 발생했습니다.' }, { status: 500 });
    }
}
