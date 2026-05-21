# 기후행동365 사이트 (Astro + Starlight)

피코 책과 동일한 Starlight + Pretendard 톤으로 만들어진 교재 사이트.

## 구조

```
site/
├── astro.config.mjs           # 사이드바·언어·CSS 설정
├── package.json
├── src/
│   ├── content.config.ts      # Starlight docs collection
│   ├── styles/custom.css      # Pretendard 폰트 + Tip/그림 박스
│   └── content/docs/
│       ├── index.mdx          # 랜딩 (CardGrid)
│       ├── intro/소개.md      # 교재 소개
│       ├── units/             # 학생용 단원 4편
│       │   ├── 01-파일럿.md
│       │   ├── 02-서버.md
│       │   ├── 03-16대.md
│       │   └── 04-운영.md
│       └── teacher/지도서.md  # 교사용 통합 지도서
```

## 로컬 실행

```bash
cd site
npm install
npm run dev
```

→ http://localhost:4321 에서 미리보기.

## 빌드 (정적 사이트 출력)

```bash
npm run build
```

→ `dist/` 폴더에 정적 HTML/CSS/JS 생성.

## 배포 옵션

### 옵션 A — GitHub Pages (무료, 학교 외부 공개)

```bash
# GitHub 저장소에 push 한 뒤 .github/workflows/deploy.yml 작성
# 또는 astro 공식 가이드: https://docs.astro.build/ko/guides/deploy/github/
```

### 옵션 B — Vercel / Netlify (무료, 가장 단순)

저장소를 Vercel·Netlify에 연결만 하면 자동 빌드·배포. 학교 도메인 연결도 가능.

### 옵션 C — 학교 서버 (라즈베리 파이 4 또는 학교 PC, 내부망 공개)

빌드 결과 `dist/` 폴더를 라즈베리 파이 4에 복사해 nginx로 띄우는 방식.

```bash
# 본인 컴퓨터에서
npm run build
scp -r dist/ pi@192.168.0.10:/var/www/climate365/

# Pi에서
sudo apt install -y nginx
sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/climate365
sudo nano /etc/nginx/sites-available/climate365  # root를 /var/www/climate365 로
sudo ln -s /etc/nginx/sites-available/climate365 /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

→ 학교 내부망에서 http://192.168.0.10/ 으로 교재 열람 가능.
대시보드(8501)·교재(80)·API(8000)가 한 서버에 공존.

## 콘텐츠 갱신

`docs/book/` 폴더의 원본 파일을 수정한 뒤, 다음 한 줄로 site로 동기화:

```bash
bash sync-docs.sh   # (생성 예정)
```

또는 site/src/content/docs/ 안의 파일을 직접 편집.

## 의존성

- Astro 5.0
- Starlight 0.30
- Pretendard 폰트 (CDN)
