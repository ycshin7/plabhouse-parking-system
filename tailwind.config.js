/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            fontFamily: {
                sans: ['Pretendard', 'system-ui', 'sans-serif'],
                display: ['GmarketSansBold', 'Pretendard', 'sans-serif'],
            },
            colors: {
                // Primary - Toss Blue 계열로 통일
                primary: {
                    50: '#EBF5FF',
                    100: '#D6EBFF',
                    200: '#ADD6FF',
                    300: '#84C1FF',
                    400: '#5AABFF',
                    500: '#3182F6',  // 메인 브랜드 컬러
                    600: '#1B64DA',
                    700: '#1350B0',
                    800: '#0D3C86',
                    900: '#07285C',
                },
                // Secondary - Purple (방문객/타워용)
                secondary: {
                    50: '#F5F3FF',
                    100: '#EDE9FE',
                    200: '#DDD6FE',
                    400: '#A78BFA',
                    500: '#8B5CF6',
                    600: '#7C3AED',
                    700: '#6D28D9',
                },
                // Surface / Neutral
                surface: {
                    DEFAULT: '#F8FAFC',
                    card: '#FFFFFF',
                    muted: '#F1F5F9',
                },
                // Semantic
                success: {
                    50: '#F0FDF4',
                    100: '#DCFCE7',
                    500: '#22C55E',
                    600: '#16A34A',
                },
                danger: {
                    50: '#FEF2F2',
                    100: '#FEE2E2',
                    500: '#EF4444',
                    600: '#DC2626',
                },
                warning: {
                    50: '#FFFBEB',
                    100: '#FEF3C7',
                    500: '#F59E0B',
                },
                // Text
                ink: {
                    DEFAULT: '#191F28',
                    secondary: '#4E5968',
                    tertiary: '#8B95A1',
                    disabled: '#B0B8C1',
                    placeholder: '#D1D6DB',
                },
                // Border
                line: {
                    DEFAULT: '#E5E8EB',
                    light: '#F2F4F6',
                },
            },
            borderRadius: {
                'card': '32px',
                'button': '24px',
                'input': '16px',
                'tag': '10px',
            },
            boxShadow: {
                'card': '0 4px 24px rgba(0, 0, 0, 0.06)',
                'card-hover': '0 8px 40px rgba(0, 0, 0, 0.1)',
                'button': '0 4px 16px rgba(49, 130, 246, 0.25)',
                'button-hover': '0 8px 24px rgba(49, 130, 246, 0.4)',
            },
            animation: {
                'fade-in': 'fadeIn 0.3s ease-out',
                'slide-up': 'slideUp 0.3s ease-out',
                'pulse-soft': 'pulseSoft 2s infinite',
            },
            keyframes: {
                fadeIn: {
                    '0%': { opacity: '0', transform: 'translateY(8px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                },
                slideUp: {
                    '0%': { transform: 'translateY(10px)', opacity: '0' },
                    '100%': { transform: 'translateY(0)', opacity: '1' },
                },
                pulseSoft: {
                    '0%, 100%': { opacity: '1' },
                    '50%': { opacity: '0.7' },
                },
            },
        },
    },
    plugins: [],
};
