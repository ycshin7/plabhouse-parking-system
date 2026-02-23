import { NextResponse } from 'next/server';

export async function GET() {
    const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
    const GITHUB_OWNER = process.env.GITHUB_OWNER;
    const GITHUB_REPO = process.env.GITHUB_REPO;
    const GITHUB_BRANCH = process.env.GITHUB_BRANCH || 'main';

    const debugInfo = {
        config: {
            hasToken: !!GITHUB_TOKEN,
            owner: GITHUB_OWNER || 'MISSING',
            repo: GITHUB_REPO || 'MISSING',
            branch: GITHUB_BRANCH,
            tokenPrefix: GITHUB_TOKEN ? GITHUB_TOKEN.substring(0, 4) + '...' : 'NONE'
        },
        env: process.env.NODE_ENV,
        currentTime: new Date().toISOString()
    };

    // GitHub API 테스트 호출
    let githubTest = null;
    if (GITHUB_TOKEN && GITHUB_OWNER && GITHUB_REPO) {
        try {
            const url = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/users.json?ref=${GITHUB_BRANCH}`;
            const res = await fetch(url, {
                headers: {
                    Authorization: `token ${GITHUB_TOKEN}`,
                    Accept: 'application/vnd.github.v3+json',
                },
                cache: 'no-store'
            });
            githubTest = {
                status: res.status,
                statusText: res.statusText,
                url: url.replace(GITHUB_TOKEN, '***')
            };
        } catch (e: any) {
            githubTest = { error: e.message };
        }
    }

    return NextResponse.json({ debugInfo, githubTest });
}
