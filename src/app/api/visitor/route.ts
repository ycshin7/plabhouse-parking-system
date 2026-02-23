import { NextRequest, NextResponse } from 'next/server';
import { loadFromGithub, saveToGithub } from '@/lib/github';

interface VisitorData {
    count: number;
    last_updated: string;
}

const DEFAULT_VISITOR: VisitorData = { count: 0, last_updated: new Date().toISOString().split('T')[0] };

export async function GET() {
    try {
        const { data } = await loadFromGithub<VisitorData>('visitor_count.json', DEFAULT_VISITOR);
        return NextResponse.json(data);
    } catch (e) {
        return NextResponse.json(DEFAULT_VISITOR);
    }
}

export async function POST(request: NextRequest) {
    try {
        const { data, sha } = await loadFromGithub<VisitorData>('visitor_count.json', DEFAULT_VISITOR);

        const today = new Date().toISOString().split('T')[0];
        data.count += 1;
        data.last_updated = today;

        await saveToGithub('visitor_count.json', data, sha, '방문자 수 업데이트');
        return NextResponse.json(data);
    } catch (e) {
        return NextResponse.json({ error: 'Failed to update visitor count' }, { status: 500 });
    }
}
