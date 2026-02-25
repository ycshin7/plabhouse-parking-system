import fs from 'fs/promises';
import path from 'path';

/**
 * GitHub 데이터 동기화 헬퍼
 * 환경변수가 있으면 GitHub을 사용하고, 없으면 로컬 JSON 파일을 사용합니다.
 */

const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const GITHUB_OWNER = process.env.GITHUB_OWNER;
const GITHUB_REPO = process.env.GITHUB_REPO;
const GITHUB_BRANCH = process.env.GITHUB_BRANCH || 'main';

const API_BASE = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents`;

interface GithubFileResponse {
    content: string;
    sha: string;
    encoding: string;
}

/**
 * 데이터를 가져옵니다 (GitHub -> 로컬 순서)
 */
export async function loadFromGithub<T>(filePath: string, defaultData: T): Promise<{ data: T; sha: string }> {
    // 1. GitHub 시도
    if (GITHUB_TOKEN && GITHUB_OWNER && GITHUB_REPO) {
        try {
            const res = await fetch(`${API_BASE}/${filePath}?ref=${GITHUB_BRANCH}`, {
                headers: {
                    Authorization: `token ${GITHUB_TOKEN}`,
                    Accept: 'application/vnd.github.v3+json',
                },
                next: { revalidate: 0 },
            });

            if (res.ok) {
                const fileData: GithubFileResponse = await res.json();
                const content = Buffer.from(fileData.content, 'base64').toString('utf-8');
                const parsed = JSON.parse(content) as T;
                return { data: parsed, sha: fileData.sha };
            }
        } catch (error) {
            console.error(`[GitHub] 로드 오류 (${filePath}):`, error);
        }
    }

    // 2. 로컬 파일 폴백
    try {
        const localPath = path.join(process.cwd(), filePath);
        const content = await fs.readFile(localPath, 'utf-8');
        return { data: JSON.parse(content) as T, sha: 'local' };
    } catch (e) {
        console.warn(`[Local] 파일 없음, 기본값 사용: ${filePath}`);
        return { data: defaultData, sha: '' };
    }
}

/**
 * 데이터를 저장합니다 (GitHub -> 로컬 순서)
 */
export async function saveToGithub<T>(
    filePath: string,
    data: T,
    sha: string,
    commitMessage: string
): Promise<boolean> {
    // 1. GitHub 시도
    if (GITHUB_TOKEN && GITHUB_OWNER && GITHUB_REPO && sha && sha !== 'local') {
        try {
            const content = Buffer.from(JSON.stringify(data, null, 2)).toString('base64');
            const body: Record<string, string> = {
                message: commitMessage,
                content,
                branch: GITHUB_BRANCH,
            };
            if (sha) body.sha = sha;

            const res = await fetch(`${API_BASE}/${filePath}`, {
                method: 'PUT',
                headers: {
                    Authorization: `token ${GITHUB_TOKEN}`,
                    Accept: 'application/vnd.github.v3+json',
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(body),
            });

            if (res.ok) {
                console.log(`[GitHub] 저장 성공: ${filePath}`);
                return true;
            }
        } catch (error) {
            console.error(`[GitHub] 저장 오류 (${filePath}):`, error);
        }
    }

    // 2. 로컬 파일 저장
    try {
        const localPath = path.join(process.cwd(), filePath);
        await fs.writeFile(localPath, JSON.stringify(data, null, 2), 'utf-8');
        console.log(`[Local] 저장 성공: ${filePath}`);
        return true;
    } catch (e) {
        console.error(`[Local] 저장 오류 (${filePath}):`, e);
        return false;
    }
}