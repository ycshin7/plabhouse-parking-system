import { NextRequest, NextResponse } from 'next/server';
import { loadFromGithub, saveToGithub } from '@/lib/github';
import { HistoryEntry, RequestsData } from '@/types';
import { stripTime } from '@/lib/allocation';

/** 임시 디버그: 환경변수 확인용 (배포 후 삭제) */
export async function GET() {
    const url = process.env.SLACK_WEBHOOK_URL || '(미설정)';
    const masked = url.length > 20 ? url.slice(0, 30) + '...' + url.slice(-10) : url;
    return NextResponse.json({ webhook_url_masked: masked, has_admin_key: !!process.env.ADMIN_KEY });
}

/**
 * POST /api/slack
 * 특정 날짜의 배정 결과를 슬랙으로 전송합니다.
 * body: { date: string, adminKey: string }
 */
export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const { date } = body;

        if (!date) {
            return NextResponse.json({ error: '날짜가 지정되지 않았습니다.' }, { status: 400 });
        }

        // 데이터 로드
        const [historyResult, requestsResult] = await Promise.all([
            loadFromGithub<HistoryEntry[]>('history.json', []),
            loadFromGithub<RequestsData>('requests.json', { target_date: '', applicants: [], guests: [], sante_opt_out: false }),
        ]);

        const { data: history, sha: historySha } = historyResult;
        const entry = history.find(h => h.date === date);

        if (!entry) {
            return NextResponse.json({ error: `${date}의 배정 결과가 존재하지 않습니다.` }, { status: 404 });
        }

        // 슬랙 메시지 구성
        const webhookUrl = process.env.SLACK_WEBHOOK_URL;
        if (!webhookUrl) {
            return NextResponse.json({ error: 'SLACK_WEBHOOK_URL 환경변수가 설정되지 않았습니다.' }, { status: 500 });
        }

        const dayNames = ["일", "월", "화", "수", "목", "금", "토"];
        const targetWeekday = dayNames[new Date(date).getDay()];

        // 상떼 여부에 따른 용량 계산 (히스토리에 용량이 없으므로 현재 requests 설정 or 기본값 참고)
        const adminCapacity = 1;
        const towerCapacity = requestsResult.data.sante_opt_out ? 3 : 2;

        const totalOccupied = entry.admin.length + entry.tower.length;
        const totalCapacity = adminCapacity + towerCapacity;
        const totalRemaining = totalCapacity - totalOccupied;
        const adminRemaining = adminCapacity - entry.admin.length;
        const towerRemaining = towerCapacity - entry.tower.length;

        let slackMsg = `📅 *${date} (${targetWeekday}) 주차 배정 결과*\n\n` +
            `🅿️ *주차 공간 현황*\n` +
            `• 전체: ${totalOccupied}/${totalCapacity} (남은 공간: ${totalRemaining})\n` +
            `• 관리실: ${entry.admin.length}/${adminCapacity} (남은 공간: ${adminRemaining})\n` +
            `• 타워: ${entry.tower.length}/${towerCapacity} (남은 공간: ${towerRemaining})\n\n` +
            `🏢 *관리실 배정*`;

        if (entry.admin.length > 0) {
            entry.admin.forEach(name => slackMsg += `\n• ${stripTime(name)}`);
        } else {
            slackMsg += `\n• (배정 없음)`;
        }

        slackMsg += `\n\n🅿️ *타워 배정*`;
        if (entry.tower.length > 0) {
            entry.tower.forEach(name => slackMsg += `\n• ${stripTime(name)}`);
        } else {
            slackMsg += `\n• (배정 없음)`;
        }

        if (entry.wait && entry.wait.length > 0) {
            slackMsg += `\n\n⏳ *대기 인원* (우선순위에서 밀림)`;
            entry.wait.forEach(name => slackMsg += `\n• ${stripTime(name)}`);
        }

        // 슬랙 전송
        const slackRes = await fetch(webhookUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: slackMsg }),
        });

        if (!slackRes.ok) {
            const errText = await slackRes.text();
            throw new Error(`Slack API error: ${slackRes.status} - ${errText}`);
        }

        // 히스토리 업데이트 (슬랙 전송됨 표시)
        entry.slack_notified = true;
        await saveToGithub('history.json', history, historySha || '', `${date} 슬랙 수동 알림 완료`);

        return NextResponse.json({ success: true });
    } catch (e: any) {
        console.error('[/api/slack] 오류:', e);
        return NextResponse.json({ error: e.message || '처리 중 오류가 발생했습니다.' }, { status: 500 });
    }
}
