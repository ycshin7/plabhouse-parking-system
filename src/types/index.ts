// 크루(사용자) 타입
export interface User {
    name: string;
    car_type: 'SUV' | 'SEDAN';
    last_parked_date: string | null;
    car_number?: string;
    car_details?: string;
}

// 방문객 타입
export interface Guest {
    name: string;
    car_type: 'SUV' | 'SEDAN';
    location: string[];
    timestamp?: string;
}

// 신청 데이터 타입
export interface RequestsData {
    target_date: string;
    applicants: Applicant[];
    guests: Guest[];
    sante_opt_out: boolean;
}

export interface Applicant {
    name: string;
    timestamp: string;
}

// 배정 히스토리 타입
export interface HistoryEntry {
    date: string;
    admin: string[];
    tower: string[];
    wait: string[];
    slack_notified?: boolean;
    created_at?: string;
}

// 배정 결과 타입
export interface AllocationResult {
    date: string;
    admin: string[];
    tower: string[];
    wait: string[];
    adminCapacity: number;
    towerCapacity: number;
}
