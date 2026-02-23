import { NextRequest, NextResponse } from 'next/server';
import { loadFromGithub, saveToGithub } from '@/lib/github';
import { User } from '@/types';

export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const { name, car_type, car_number, car_details } = body;
        if (!name) return NextResponse.json({ error: '이름을 입력해주세요.' }, { status: 400 });

        const { data: users, sha } = await loadFromGithub<User[]>('users.json', []);
        if (users.some((u) => u.name === name))
            return NextResponse.json({ error: '이미 등록된 이름입니다.' }, { status: 409 });

        users.push({
            name,
            car_type: car_type || 'SEDAN',
            car_number: car_number || '',
            car_details: car_details || '',
            last_parked_date: null
        });
        await saveToGithub('users.json', users, sha, `직원 추가: ${name}`);
        return NextResponse.json({ success: true });
    } catch (e) {
        return NextResponse.json({ error: '처리 중 오류가 발생했습니다.' }, { status: 500 });
    }
}

export async function PUT(request: NextRequest) {
    try {
        const body = await request.json();
        const { index, name, car_type, car_number, car_details } = body;

        const { data: users, sha } = await loadFromGithub<User[]>('users.json', []);
        if (index < 0 || index >= users.length)
            return NextResponse.json({ error: '잘못된 인덱스입니다.' }, { status: 400 });

        const oldName = users[index].name;

        // 이름이 바뀌는 경우 중복 체크
        if (name !== oldName && users.some(u => u.name === name)) {
            return NextResponse.json({ error: '이미 존재하는 이름입니다.' }, { status: 409 });
        }

        users[index] = {
            ...users[index],
            name,
            car_type: car_type || 'SEDAN',
            car_number: car_number || '',
            car_details: car_details || ''
        };

        await saveToGithub('users.json', users, sha, `직원 수정: ${oldName} → ${name}`);
        return NextResponse.json({ success: true });
    } catch (e) {
        return NextResponse.json({ error: '처리 중 오류가 발생했습니다.' }, { status: 500 });
    }
}

export async function DELETE(request: NextRequest) {
    try {
        const { index } = await request.json();
        const { data: users, sha } = await loadFromGithub<User[]>('users.json', []);
        if (index < 0 || index >= users.length)
            return NextResponse.json({ error: '잘못된 인덱스입니다.' }, { status: 400 });

        const name = users[index].name;
        users.splice(index, 1);
        await saveToGithub('users.json', users, sha, `직원 삭제: ${name}`);
        return NextResponse.json({ success: true });
    } catch (e) {
        return NextResponse.json({ error: '처리 중 오류가 발생했습니다.' }, { status: 500 });
    }
}
