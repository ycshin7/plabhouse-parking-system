/**
 * 배정 알고리즘
 * 기존 auto_allocate.py의 Python 로직을 TypeScript로 이식
 */

import { User, Guest, Applicant, HistoryEntry } from '@/types';

export interface AllocationInput {
    users: User[];
    history: HistoryEntry[];
    applicants: Applicant[];
    guests: Guest[];
    santeOptOut: boolean;
    targetDate: string;
}

export interface AllocationOutput {
    admin: string[];
    tower: string[];
    wait: string[];
    adminCapacity: number;
    towerCapacity: number;
}

interface Candidate {
    type: 'staff' | 'guest';
    name: string;
    carType: string;
    lastParked: string;
    timestamp: Date;
    displayName: string;
    location?: string[];
}

/**
 * 이름에서 시간 부분을 제거합니다.
 * 예: "뚜비 (SUV) 18:00" → "뚜비 (SUV)"
 */
export function stripTime(nameStr: string): string {
    const parts = nameStr.rsplit ? nameStr.rsplit(' ', 1) : nameStr.split(' ');
    const lastPart = parts[parts.length - 1];
    if (/^\d{1,2}:\d{2}$/.test(lastPart) || lastPart === '수동입력') {
        return parts.slice(0, -1).join(' ');
    }
    return nameStr;
}

/**
 * 이름에서 마지막 주차 날짜를 히스토리에서 동적으로 계산합니다.
 */
function getLastParkedFromHistory(name: string, history: HistoryEntry[]): string {
    let lastParked = '1900-01-01';
    for (const entry of history) {
        const allParked = [...entry.admin, ...entry.tower];
        for (const nameStr of allParked) {
            const baseName = nameStr.split(' (')[0];
            if (baseName === name) {
                if (entry.date > lastParked) {
                    lastParked = entry.date;
                }
            }
        }
    }
    return lastParked;
}

/**
 * 주차 배정 알고리즘 실행
 */
export function runAllocation(input: AllocationInput): AllocationOutput {
    const { users, history, applicants, guests, santeOptOut, targetDate } = input;

    let adminSlots = 1;
    let towerSlots = santeOptOut ? 3 : 2;
    const adminCapacity = adminSlots;
    const towerCapacity = towerSlots;

    const staffCandidates: Candidate[] = [];
    const guestCandidates: Candidate[] = [];

    // 크루 지원자 처리
    for (const app of applicants) {
        let ts = new Date(0);
        let uTime = '00:00';

        try {
            ts = new Date(app.timestamp);
            // KST 변환
            const kstOffset = 9 * 60 * 60 * 1000;
            const utcTime = ts.getTime();
            const kstTime = new Date(utcTime);
            uTime = kstTime.toLocaleTimeString('ko-KR', {
                hour: '2-digit',
                minute: '2-digit',
                hour12: false,
                timeZone: 'Asia/Seoul',
            });
        } catch {
            ts = new Date(0);
        }

        const userObj = users.find((u) => u.name === app.name);
        const carType = userObj?.car_type || 'SEDAN';

        // 히스토리에서 최근 주차일 동적 계산
        const lastParked = getLastParkedFromHistory(app.name, history);

        staffCandidates.push({
            type: 'staff',
            name: app.name,
            carType,
            lastParked,
            timestamp: ts,
            displayName: `${app.name} (${carType}) ${uTime}`,
        });
    }

    // 방문객 처리
    for (const g of guests) {
        let ts = new Date(0);
        let timeStr = '00:00';

        if (g.timestamp) {
            try {
                ts = new Date(g.timestamp);
                timeStr = ts.toLocaleTimeString('ko-KR', {
                    hour: '2-digit',
                    minute: '2-digit',
                    hour12: false,
                    timeZone: 'Asia/Seoul',
                });
            } catch {
                ts = new Date(0);
            }
        }

        guestCandidates.push({
            type: 'guest',
            name: g.name,
            carType: g.car_type,
            lastParked: '1900-01-01',
            timestamp: ts,
            displayName: `${g.name} (${g.car_type}) ${timeStr}`,
            location: g.location,
        });
    }

    // 정렬: 크루는 최근주차일 오름차순 → 신청시간 오름차순
    staffCandidates.sort((a, b) => {
        const dateCompare = a.lastParked.localeCompare(b.lastParked);
        if (dateCompare !== 0) return dateCompare;
        return a.timestamp.getTime() - b.timestamp.getTime();
    });

    // 정렬: 방문객은 신청시간 오름차순
    guestCandidates.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());

    const resultAdmin: string[] = [];
    const resultTower: string[] = [];
    const resultWait: string[] = [];

    // 1. 방문객 우선 배정
    for (const g of guestCandidates) {
        let assigned = false;
        const loc = g.location || ['상관없음'];

        if (loc.includes('관리실')) {
            if (adminSlots > 0) {
                resultAdmin.push(g.displayName);
                adminSlots--;
                assigned = true;
            }
        } else if (loc.includes('타워')) {
            if (towerSlots > 0) {
                resultTower.push(g.displayName);
                towerSlots--;
                assigned = true;
            }
        } else {
            if (towerSlots > 0) {
                resultTower.push(g.displayName);
                towerSlots--;
                assigned = true;
            } else if (adminSlots > 0) {
                resultAdmin.push(g.displayName);
                adminSlots--;
                assigned = true;
            }
        }

        if (!assigned) {
            resultWait.push(g.displayName);
        }
    }

    // 2. 크루 배정
    for (const s of staffCandidates) {
        let assigned = false;

        if (s.carType === 'SUV') {
            if (adminSlots > 0) {
                resultAdmin.push(s.displayName);
                adminSlots--;
                assigned = true;
            }
        } else {
            if (towerSlots > 0) {
                resultTower.push(s.displayName);
                towerSlots--;
                assigned = true;
            } else if (adminSlots > 0) {
                resultAdmin.push(s.displayName);
                adminSlots--;
                assigned = true;
            }
        }

        if (!assigned) {
            resultWait.push(s.displayName);
        }
    }

    return {
        admin: resultAdmin,
        tower: resultTower,
        wait: resultWait,
        adminCapacity,
        towerCapacity,
    };
}

// String.prototype에 rsplit 추가 (Python 호환)
declare global {
    interface String {
        rsplit(sep: string, maxsplit: number): string[];
    }
}

String.prototype.rsplit = function (sep: string, maxsplit: number): string[] {
    const parts = this.split(sep);
    if (maxsplit && parts.length > maxsplit) {
        const result = parts.slice(-(maxsplit + 1));
        result[0] = parts.slice(0, parts.length - maxsplit).join(sep);
        return result;
    }
    return parts;
};
