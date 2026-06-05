import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
  site: 'https://greatsong.github.io',
  base: '/climate-action-365',
  integrations: [
    starlight({
      title: '기후행동365 · 교실 환경 모니터링',
      description: '당곡고 16개 교실 IoT 환경 모니터링 시스템 — 피코 + 마이크로파이썬 + 실시간 대시보드',
      defaultLocale: 'root',
      locales: {
        root: { label: '한국어', lang: 'ko' },
      },
      sidebar: [
        {
          label: '들어가며',
          items: [
            { label: '교재 소개', slug: 'intro/소개' },
          ],
        },
        {
          label: '학생용 단원',
          autogenerate: { directory: 'units' },
        },
        {
          label: '교사용',
          autogenerate: { directory: 'teacher' },
        },
      ],
      customCss: ['./src/styles/custom.css'],
      lastUpdated: true,
      pagination: true,
    }),
  ],
});
