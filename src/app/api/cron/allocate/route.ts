import { NextRequest, NextResponse } from 'next/server';
import { loadFromGithub, saveToGithub } from '@/lib/github';
import { User, RequestsData, HistoryEntry } from '@/types';
import { runAllocation, stripTime } from '@/lib/allocation';
import { getKSTNow, getKSTDateString } from '@/lib/kst';

const DEFAULT_REQUESTS: RequestsData = {
    target_date: '',
    applicants: [],
    guests: [],
    sante_opt_out: false,
};

/**
 * GET /api/cron/allocate
 * Vercel Cron으로 호출되는 자동 배정 엔드포인트
 * 매일 00:01 KST (15:01 UTC) 실행
 */
export async function GET(request: NextRequest) {
    try {
        console.log('[cron] === 크론 배정 시작 ===');

        // CRON_SECRET 검증
        const authHeader = request.headers.get('authorization');
        const cronSecret = process.env.CRON_SECRET;
        if (cronSecret && authHeader !== `Bearer ${cronSecret}`) {
            console.error('[cron] 인증 실패');
            return NextResponse.json({ error: '권한이 없습니다.' }, { status: 401 });
        }

        const kst = getKSTNow();
        const today = getKSTDateString();
        const day = kst.getDay();
        console.log(`[cron] KST: ${today}, 요일: ${day}, UTC: ${new Date().toISOString()}`);

        // 주말이면 skip
        if (day === 0 || day === 6) {
            console.log(`[cron] 주말 skip (day=${day})`);
            return NextResponse.json({ skipped: true, reason: '주말은 배정하지 않습니다.', date: today });
        }

        // 데이터 로드
        const [usersResult, requestsResult, historyResult] = await Promise.all([
            loadFromGithub<User[]>('users.json', []),
            loadFromGithub<RequestsData>('requests.json', DEFAULT_REQUESTS),
            loadFromGithub<HistoryEntry[]>('history.json', []),
        ]);

        const { data: users } = usersResult;
        const { data: requestsData, sha: requestsSha } = requestsResult;
        const { data: history, sha: historySha } = historyResult;

        console.log(`[cron] 데이터 로드 완료 - users: ${users.length}명, applicants: ${requestsData.applicants?.length || 0}명, guests: ${requestsData.guests?.length || 0}명, history SHA: ${historySha ? '있음' : '없음'}`);

        // 이미 오늘 배정이 완료되었으면 skip, 단 slack 알림이 안갔으면 재시도
        const existingEntry = history.find((h) => h.date === today);
        if (existingEntry) {
            if (existingEntry.slack_notified) {
                console.log(`[cron] 이미 배정+알림 완료 skip: ${today}`);
                return NextResponse.json({ skipped: true, reason: `${today} 배정이 이미 완료되었습니다.`, date: today });
            } else {
                console.log(`[cron] 배정은 되었으나 알림 실패. 슬랙 알림 재시도: ${today}`);
                
                let slackNotified = false;
                const webhookUrl = process.env.SLACK_WEBHOOK_URL;
                if (webhookUrl) {
                    const dayNames = ['일', '월', '화', '수', '목', '금', '토'];
                    const targetWeekday = dayNames[new Date(today).getDay()];
                    
                    const adminCapacity = 1;
                    const towerCapacity = requestsData.sante_opt_out ? 3 : 2;

                    let slackMsg = `📅 *${today} (${targetWeekday}) 주차 배정 결과*\n\n` +
                        `🅿️ *주차 공간 현황*\n` +
                        `• 전체: ${existingEntry.admin.length + existingEntry.tower.length}/${adminCapacity + towerCapacity}\n` +
                        `• 관리실: ${existingEntry.admin.length}/${adminCapacity}\n` +
                        `• 타워: ${existingEntry.tower.length}/${towerCapacity}\n\n` +
                        `🏢 *관리실 배정*`;

                    if (existingEntry.admin.length > 0) {
                        existingEntry.admin.forEach(name => slackMsg += `\n• ${stripTime(name)}`);
                    } else {
                        slackMsg += `\n• (배정 없음)`;
                    }

                    slackMsg += `\n\n🅿️ *타워 배정*`;
                    if (existingEntry.tower.length > 0) {
                        existingEntry.tower.forEach(name => slackMsg += `\n• ${stripTime(name)}`);
                    } else {
                        slackMsg += `\n• (배정 없음)`;
                    }

                    if (existingEntry.wait.length > 0) {
                        slackMsg += `\n\n⏳ *대기 인원*`;
                        existingEntry.wait.forEach(name => slackMsg += `\n• ${stripTime(name)}`);
                    }

                    try {
                        const slackRes = await fetch(webhookUrl, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ text: slackMsg }),
                        });
                        if (slackRes.ok) {
                            slackNotified = true;
                        } else {
                            console.error(`[cron] Slack 재전송 실패: ${slackRes.status} - ${await slackRes.text()}`);
                        }
                    } catch (e) {
                        console.error('[cron] Slack 네트워크 오류:', e);
                    }
                }

                if (slackNotified) {
                    existingEntry.slack_notified = true;
                    const historySaved = await saveToGithub('history.json', history, historySha || '', `[cron] 자동 배정 Slack 재알림: ${today}`);
                    return NextResponse.json({ success: true, message: '슬랙 알림 재전송 성공', historySaved, date: today });
                } else {
                    return NextResponse.json({ error: '슬랙 알림 재전송 실패' }, { status: 500 });
                }
            }
        }

        // 신청자가 없으면 skip
        if (!requestsData.applicants?.length && !requestsData.guests?.length) {
            console.log('[cron] 신청자 없음 skip');
            return NextResponse.json({ skipped: true, reason: '신청 인원이 없습니다.', date: today });
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
        let slackNotified = false;
        const webhookUrl = process.env.SLACK_WEBHOOK_URL;
        if (webhookUrl) {
            const dayNames = ['일', '월', '화', '수', '목', '금', '토'];
            const targetWeekday = dayNames[new Date(today).getDay()];

            let slackMsg = `📅 *${today} (${targetWeekday}) 주차 배정 결과*\n\n` +
                `🅿️ *주차 공간 현황*\n` +
                `• 전체: ${result.admin.length + result.tower.length}/${result.adminCapacity + result.towerCapacity}\n` +
                `• 관리실: ${result.admin.length}/${result.adminCapacity}\n` +
                `• 타워: ${result.tower.length}/${result.towerCapacity}\n\n` +
                `🏢 *관리실 배정*`;

            if (result.admin.length > 0) {
                result.admin.forEach(name => slackMsg += `\n• ${stripTime(name)}`);
            } else {
                slackMsg += `\n• (배정 없음)`;
            }

            slackMsg += `\n\n🅿️ *타워 배정*`;
            if (result.tower.length > 0) {
                result.tower.forEach(name => slackMsg += `\n• ${stripTime(name)}`);
            } else {
                slackMsg += `\n• (배정 없음)`;
            }

            if (result.wait.length > 0) {
                slackMsg += `\n\n⏳ *대기 인원*`;
                result.wait.forEach(name => slackMsg += `\n• ${stripTime(name)}`);
            }

            try {
                const slackRes = await fetch(webhookUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: slackMsg }),
                });
                if (slackRes.ok) {
                    slackNotified = true;
                } else {
                    const errText = await slackRes.text();
                    console.error(`[cron] Slack 전송 실패: ${slackRes.status} - ${errText}`);
                }
            } catch (e) {
                console.error('[cron] Slack 네트워크 오류:', e);
            }
        } else {
            console.error('[cron] SLACK_WEBHOOK_URL 환경변수가 설정되지 않았습니다.');
        }

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

        // 순차 저장 (GitHub API는 동시 커밋 시 SHA 충돌 발생)
        const historySaved = await saveToGithub('history.json', newHistory, historySha || '', `[cron] 자동 배정: ${today}`);
        if (!historySaved) {
            console.error(`[cron] history.json 저장 실패`);
            return NextResponse.json({ error: '배정 결과 저장에 실패했습니다.' }, { status: 500 });
        }

        const requestsSaved = await saveToGithub('requests.json', updatedRequests, requestsSha || '', `[cron] 신청 초기화: ${today}`);
        const usersSaved = await saveToGithub('users.json', users, usersResult.sha || '', `[cron] 마지막주차일 업데이트: ${today}`);

        if (!requestsSaved || !usersSaved) {
            console.error(`[cron] 저장 부분 실패 - requests:${requestsSaved} users:${usersSaved}`);
        }

        console.log(`[cron] === 배정 완료 === date: ${today}, slack: ${slackNotified}, history: ${historySaved}, requests: ${requestsSaved}, users: ${usersSaved}`);

        return NextResponse.json({
            success: true,
            date: today,
            slack_notified: slackNotified,
            result: {
                admin: result.admin,
                tower: result.tower,
                wait: result.wait,
            },
        });
    } catch (error) {
        console.error('[/api/cron/allocate] 오류:', error);
        return NextResponse.json({ error: '자동 배정 처리 중 오류가 발생했습니다.' }, { status: 500 });
    }
}
