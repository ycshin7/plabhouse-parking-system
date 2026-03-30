import { NextRequest, NextResponse } from 'next/server';
import { loadFromGithub, saveToGithub } from '@/lib/github';
import { User, RequestsData, HistoryEntry } from '@/types';
import { runAllocation, stripTime } from '@/lib/allocation';
import { getKSTDateString } from '@/lib/kst';

const DEFAULT_REQUESTS: RequestsData = {
    target_date: '',
    applicants: [],
    guests: [],
    sante_opt_out: false,
};

/**
 * POST /api/allocate
 * 배정 알고리즘 실행 (어드민 전용)
 * body: { adminKey: string, targetDate: string }
 */
export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const { adminKey, targetDate } = body;

        // 어드민 키 검증
        const validKey = process.env.ADMIN_KEY;
        if (validKey && adminKey !== validKey) {
            return NextResponse.json({ error: '권한이 없습니다.' }, { status: 403 });
        }

        return await processAllocation(targetDate);
    } catch (error) {
        console.error('[/api/allocate] POST 오류:', error);
        return NextResponse.json({ error: '배정 처리 중 오류가 발생했습니다.' }, { status: 500 });
    }
}

/**
 * GET /api/allocate
 * Vercel Cron을 위한 엔드포인트
 */
export async function GET(request: NextRequest) {
    // Vercel Cron 인증 (배포 환경에서만 동작)
    const authHeader = request.headers.get('authorization');
    if (process.env.CRON_SECRET && authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    try {
        return await processAllocation(undefined);
    } catch (error) {
        console.error('[/api/allocate] GET 오류:', error);
        return NextResponse.json({ error: '배정 처리 중 오류가 발생했습니다.' }, { status: 500 });
    }
}

async function processAllocation(targetDate?: string) {
    // 데이터 로드
    const [usersResult, requestsResult, historyResult] = await Promise.all([
        loadFromGithub<User[]>('users.json', []),
        loadFromGithub<RequestsData>('requests.json', DEFAULT_REQUESTS),
        loadFromGithub<HistoryEntry[]>('history.json', []),
    ]);

    const { data: users } = usersResult;
    const { data: requestsData, sha: requestsSha } = requestsResult;
    const { data: history, sha: historySha } = historyResult;

    const today = targetDate || getKSTDateString();

    const existingEntry = history.find((h) => h.date === today);

    // 슬랙 재시도 로직: 배정은 성공했으나 슬랙 알림이 실패한 경우
    if (existingEntry) {
        if (existingEntry.slack_notified) {
            return NextResponse.json({
                error: `${today} 배정이 이미 완료되었습니다.`,
                existing: existingEntry,
            }, { status: 409 });
        } else {
            console.log(`[${today}] 슬랙 알림 재시도 중...`);
            
            // Result 구성 (기존 데이터를 기반으로)
            const adminCapacity = 1;
            const towerCapacity = requestsData.sante_opt_out ? 3 : 2; // 혹은 이미 알고 있는 용량 사용.
            // 하지만 existingEntry에는 배정명단이 있으니 그대로 슬랙 포맷만 만듭니다.
            const result = {
                admin: existingEntry.admin,
                tower: existingEntry.tower,
                wait: existingEntry.wait,
                adminCapacity,
                towerCapacity
            };
            
            const slackSuccess = await sendSlackNotification(today, result);
            
            if (slackSuccess) {
                // 히스토리 업데이트
                existingEntry.slack_notified = true;
                await saveToGithub('history.json', history, historySha || '', `Slack 알림 재시도 완료: ${today}`);
                return NextResponse.json({ success: true, message: '슬랙 알림 재전송 성공', existing: existingEntry });
            } else {
                return NextResponse.json({ error: '슬랙 알림 재전송 실패' }, { status: 500 });
            }
        }
    }

    if (!requestsData.applicants?.length && !requestsData.guests?.length) {
        return NextResponse.json({ error: '신청 인원이 없습니다.' }, { status: 400 });
    }

    // 배정 실행
    const result = runAllocation({
        users,
        history,
        applicants: requestsData.applicants || [],
        guests: requestsData.guests || [],
        santeOptOut: requestsData.sante_opt_out || false,
    });

    // 슬랙 알림 전송 (저장 전에 시도하여 slack_notified 상태 결정)
    const slackNotified = await sendSlackNotification(today, result);

    // 히스토리 엔트리 생성 (Slack 결과 반영)
    const historyEntry: HistoryEntry = {
        date: today,
        admin: result.admin,
        tower: result.tower,
        wait: result.wait,
        slack_notified: slackNotified,
        created_at: new Date().toISOString(),
    };

    const newHistory = history.filter((h) => h.date !== today);
    newHistory.push(historyEntry);
    newHistory.sort((a, b) => b.date.localeCompare(a.date));

    // users.json 업데이트 (last_parked_date)
    const assignedNames = [...result.admin, ...result.tower].map((n) => n.split(' (')[0]);
    for (const user of users) {
        if (assignedNames.includes(user.name)) {
            user.last_parked_date = today;
        }
    }

    // 신청 목록 초기화
    const updatedRequests: RequestsData = {
        ...requestsData,
        applicants: [],
        guests: [],
    };

    // 동시 저장 (단일 저장으로 SHA 이슈 해결)
    const [historySaved, requestsSaved, usersSaved] = await Promise.all([
        saveToGithub('history.json', newHistory, historySha || '', `자동 배정: ${today}`),
        saveToGithub('requests.json', updatedRequests, requestsSha || '', `신청 초기화: ${today}`),
        saveToGithub('users.json', users, usersResult.sha || '', `마지막주차일 업데이트: ${today}`),
    ]);

    if (!historySaved || !requestsSaved || !usersSaved) {
        console.error(`[/api/allocate] 저장 실패 - history:${historySaved} requests:${requestsSaved} users:${usersSaved}`);
        if (!historySaved) {
            return NextResponse.json({ error: '배정 결과 저장에 실패했습니다.' }, { status: 500 });
        }
    }

    return NextResponse.json({
        success: true,
        result: {
            date: today,
            ...result,
        },
    });
}

/**
 * 슬랙 알림 전송 헬퍼 함수
 */
async function sendSlackNotification(today: string, result: any): Promise<boolean> {
    const webhookUrl = process.env.SLACK_WEBHOOK_URL;
    if (!webhookUrl) return false;

    try {
        const dayNames = ['일', '월', '화', '수', '목', '금', '토'];
        const targetWeekday = dayNames[new Date(today).getDay()];

        // result에 capacity가 있으면 사용하고, 없으면 기본값(1, 2) 적용 (재시도 시를 위해)
        const adminCapacity = result.adminCapacity || 1;
        const towerCapacity = result.towerCapacity || 2; 

        let slackMsg = `📅 *${today} (${targetWeekday}) 주차 배정 결과*\n\n` +
            `🅿️ *주차 공간 현황*\n` +
            `• 전체: ${result.admin.length + result.tower.length}/${adminCapacity + towerCapacity}\n` +
            `• 관리실: ${result.admin.length}/${adminCapacity}\n` +
            `• 타워: ${result.tower.length}/${towerCapacity}\n\n` +
            `🏢 *관리실 배정*`;

        if (result.admin.length > 0) {
            result.admin.forEach((name: string) => slackMsg += `\n• ${stripTime(name)}`);
        } else {
            slackMsg += `\n• (배정 없음)`;
        }

        slackMsg += `\n\n🅿️ *타워 배정*`;
        if (result.tower.length > 0) {
            result.tower.forEach((name: string) => slackMsg += `\n• ${stripTime(name)}`);
        } else {
            slackMsg += `\n• (배정 없음)`;
        }

        if (result.wait.length > 0) {
            slackMsg += `\n\n⏳ *대기 인원*`;
            result.wait.forEach((name: string) => slackMsg += `\n• ${stripTime(name)}`);
        }

        await fetch(webhookUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: slackMsg }),
        });
        return true;
    } catch (e) {
        console.error('Slack notification failed:', e);
        return false;
    }
}
