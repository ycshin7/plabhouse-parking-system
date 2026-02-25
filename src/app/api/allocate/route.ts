import { NextRequest, NextResponse } from 'next/server';
import { loadFromGithub, saveToGithub } from '@/lib/github';
import { User, RequestsData, HistoryEntry } from '@/types';
import { runAllocation } from '@/lib/allocation';

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

        // 데이터 로드
        const [usersResult, requestsResult, historyResult] = await Promise.all([
            loadFromGithub<User[]>('users.json', []),
            loadFromGithub<RequestsData>('requests.json', DEFAULT_REQUESTS),
            loadFromGithub<HistoryEntry[]>('history.json', []),
        ]);

        const { data: users } = usersResult;
        const { data: requestsData, sha: requestsSha } = requestsResult;
        const { data: history, sha: historySha } = historyResult;

        // 중복 배정 방지
        const today = targetDate || new Date().toLocaleDateString('ko-KR', {
            timeZone: 'Asia/Seoul',
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
        }).replace(/\./g, '-').replace(/ /g, '').slice(0, 10);

        const existingEntry = history.find((h) => h.date === today);
        if (existingEntry && existingEntry.slack_notified) {
            return NextResponse.json({
                error: `${today} 배정이 이미 완료되었습니다.`,
                existing: existingEntry,
            }, { status: 409 });
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
            targetDate: today,
        });

        // 히스토리에 저장
        const historyEntry: HistoryEntry = {
            date: today,
            admin: result.admin,
            tower: result.tower,
            wait: result.wait,
            slack_notified: false,
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

        // 동시 저장
        const [historySaved, requestsSaved, usersSaved] = await Promise.all([
            saveToGithub('history.json', newHistory, historySha || '', `자동 배정: ${today}`),
            saveToGithub('requests.json', updatedRequests, requestsSha || '', `신청 초기화: ${today}`),
            saveToGithub('users.json', users, usersResult.sha || '', `마지막주차일 업데이트: ${today}`),
        ]);

        if (!historySaved) {
            return NextResponse.json({ error: '배정 결과 저장에 실패했습니다.' }, { status: 500 });
        }

        // 슬랙 알림 전송
        const webhookUrl = process.env.SLACK_WEBHOOK_URL;
        if (webhookUrl) {
            const dayNames = ["일", "월", "화", "수", "목", "금", "토"];
            const targetWeekday = dayNames[new Date(today).getDay()];
            const adminCapacity = 1;
            const towerCapacity = requestsData.sante_opt_out ? 3 : 2;

            const stripTime = (nameStr: string) => {
                const parts = nameStr.split(' ');
                const last = parts[parts.length - 1];
                if (/^\d{1,2}:\d{2}$/.test(last) || last === '수동입력') {
                    return parts.slice(0, -1).join(' ');
                }
                return nameStr;
            };

            let slackMsg = `📅 **${today} (${targetWeekday}) 주차 배정 결과**\n\n` +
                `🅿️ **주차 공간 현황**\n` +
                `• 전체: ${result.admin.length + result.tower.length}/${adminCapacity + towerCapacity}\n` +
                `• 관리실: ${result.admin.length}/${adminCapacity}\n` +
                `• 타워: ${result.tower.length}/${towerCapacity}\n\n` +
                `🏢 **관리실 배정**`;

            if (result.admin.length > 0) {
                result.admin.forEach(name => slackMsg += `\n• ${stripTime(name)}`);
            } else {
                slackMsg += `\n• (배정 없음)`;
            }

            slackMsg += `\n\n🅿️ **타워 배정**`;
            if (result.tower.length > 0) {
                result.tower.forEach(name => slackMsg += `\n• ${stripTime(name)}`);
            } else {
                slackMsg += `\n• (배정 없음)`;
            }

            if (result.wait.length > 0) {
                slackMsg += `\n\n⏳ **대기 인원**`;
                result.wait.forEach(name => slackMsg += `\n• ${stripTime(name)}`);
            }

            try {
                await fetch(webhookUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: slackMsg }),
                });

                // 히스토리에 슬랙 전송 완료 표시 업데이트
                historyEntry.slack_notified = true;
                await saveToGithub('history.json', newHistory, '', `Slack 알림 완료: ${today}`);
            } catch (e) {
                console.error('Slack notification failed:', e);
            }
        }

        return NextResponse.json({
            success: true,
            result: {
                date: today,
                ...result,
            },
        });
    } catch (error) {
        console.error('[/api/allocate] 오류:', error);
        return NextResponse.json({ error: '배정 처리 중 오류가 발생했습니다.' }, { status: 500 });
    }
}
