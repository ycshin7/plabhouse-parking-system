/**
 * 서버사이드 KST(한국 표준시) 유틸리티
 */

/** 현재 KST 시간 정보를 반환 */
export function getKSTNow(): Date {
    const now = new Date();
    const formatter = new Intl.DateTimeFormat('en-US', {
        timeZone: 'Asia/Seoul',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
    });
    const parts = formatter.formatToParts(now);
    const get = (type: string) => parts.find(p => p.type === type)?.value || '0';
    return new Date(
        parseInt(get('year')),
        parseInt(get('month')) - 1,
        parseInt(get('day')),
        parseInt(get('hour')),
        parseInt(get('minute')),
        parseInt(get('second'))
    );
}

/** 현재 KST 날짜를 YYYY-MM-DD로 반환 */
export function getKSTDateString(): string {
    const kst = getKSTNow();
    const y = kst.getFullYear();
    const m = String(kst.getMonth() + 1).padStart(2, '0');
    const d = String(kst.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
}

/** 평일 00:00~00:05 KST 사이 신청 차단 여부 */
export function isApplicationClosed(): { closed: boolean; message: string } {
    const kst = getKSTNow();
    const day = kst.getDay(); // 0=일, 6=토
    const hour = kst.getHours();
    const minute = kst.getMinutes();

    // 주말은 차단하지 않음 (월요일용 신청 누적)
    if (day === 0 || day === 6) return { closed: false, message: '' };

    // 평일 00:00~00:05: 배정 처리 중 차단
    if (hour === 0 && minute < 5) {
        return { closed: true, message: '자정 마감 후 배정 처리 중입니다. 00:05 이후 다시 신청해주세요.' };
    }

    return { closed: false, message: '' };
}
