import { NextRequest, NextResponse } from 'next/server';

/**
 * GET /api/github-check
 * GitHub 연동 상태를 진단하고 리포트를 반환합니다.
 */
export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const { adminKey } = body;

        // 어드민 키 검증
        const validKey = process.env.ADMIN_KEY;
        if (validKey && adminKey !== validKey) {
            return NextResponse.json({ error: '권한이 없습니다.' }, { status: 403 });
        }

        const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
        const GITHUB_OWNER = process.env.GITHUB_OWNER;
        const GITHUB_REPO = process.env.GITHUB_REPO;

        const report = {
            env: {
                token: !!GITHUB_TOKEN,
                owner: !!GITHUB_OWNER,
                repo: !!GITHUB_REPO,
            },
            status: 'unknown',
            message: '',
            details: {} as any,
        };

        if (!GITHUB_TOKEN || !GITHUB_OWNER || !GITHUB_REPO) {
            report.status = 'error';
            report.message = '환경변수(GITHUB_TOKEN, OWNER, REPO)가 설정되지 않았습니다.';
            return NextResponse.json(report);
        }

        // 1. GitHub API 연결 테스트 (사용자 정보 확인)
        try {
            const userRes = await fetch('https://api.github.com/user', {
                headers: {
                    Authorization: `token ${GITHUB_TOKEN}`,
                    Accept: 'application/vnd.github.v3+json',
                },
            });

            if (!userRes.ok) {
                report.status = 'error';
                report.message = `GitHub 인증 실패 (Status: ${userRes.status})`;
                return NextResponse.json(report);
            }

            const userData = await userRes.json();
            report.details.user = userData.login;

            // 2. 저장소 접근 확인
            const repoRes = await fetch(`https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}`, {
                headers: {
                    Authorization: `token ${GITHUB_TOKEN}`,
                    Accept: 'application/vnd.github.v3+json',
                },
            });

            if (!repoRes.ok) {
                report.status = 'error';
                report.message = `저장소 접근 실패 (Owner/Repo 확인 필요, Status: ${repoRes.status})`;
                return NextResponse.json(report);
            }

            const repoData = await repoRes.json();
            report.details.repo = repoData.full_name;
            report.details.private = repoData.private;

            // 3. 파일 목록 확인 (데이터 정합성)
            const contentsRes = await fetch(`https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents`, {
                headers: {
                    Authorization: `token ${GITHUB_TOKEN}`,
                    Accept: 'application/vnd.github.v3+json',
                },
            });

            if (contentsRes.ok) {
                const contents = await contentsRes.json();
                const files = Array.isArray(contents) ? contents.map((f: any) => f.name) : [];
                report.details.files = files;

                const requiredFiles = ['users.json', 'requests.json', 'history.json'];
                const missing = requiredFiles.filter(f => !files.includes(f));

                if (missing.length > 0) {
                    report.status = 'warning';
                    report.message = `연결은 성공했으나 필수 파일(${missing.join(', ')})이 저장소에 없습니다.`;
                } else {
                    report.status = 'success';
                    report.message = `GitHub 연결 성공! (계정: ${userData.login}, 저장소: ${repoData.full_name})`;
                }
            } else {
                report.status = 'warning';
                report.message = '저장소 연결은 성공했으나 파일 목록을 가져오지 못했습니다.';
            }

            return NextResponse.json(report);
        } catch (e: any) {
            report.status = 'error';
            report.message = `API 호출 중 오류: ${e.message}`;
            return NextResponse.json(report);
        }
    } catch (e: any) {
        return NextResponse.json({ error: '잘못된 요청입니다.' }, { status: 400 });
    }
}
