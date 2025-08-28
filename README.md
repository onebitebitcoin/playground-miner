# Playground Miner (Vue3 + Tailwind + Django)

본 저장소는 간단한 게임 플레이그라운드를 위한 예제로, 첫 번째 게임으로 "비트코인 채굴(간이)"을 제공합니다. 프론트엔드는 Vue 3 + TailwindCSS, 백엔드는 Django 기반 API + SSE(Server-Sent Events)로 실시간 블록 방송을 수행합니다.

브라우저 환경상 순수 TCP 소켓으로는 직접 연결할 수 없기 때문에, HTTP 위에서 동작하는 SSE로 실시간 동기화를 구현했습니다. 요구사항의 "TCP 서버"는 브라우저-서버 간 실시간 통신 맥락에서 WebSocket/SSE 계열로 해석하시면 됩니다. 필요 시 순수 TCP 서버(별도 포트)도 Django 관리커맨드로 확장 가능합니다.

## 폴더 구조

- `frontend/` — Vue 3 + Vite + Tailwind UI
- `backend/` — Django API 및 SSE 엔드포인트

## 채굴 규칙(요약)

- 난수 범위: 1 ~ 100000
- 초기 난이도(허용 최대값): 10000
- 블록이 10개 채워질 때마다 난이도를 절반으로 낮춤(허용 최대값 감소)
- 조건: 생성된 난수 ≤ 현재 난이도일 때 채굴 성공, 서버에 제출 시 블록이 생성됩니다.

난이도 함수는 `height`(현재까지 생성된 블록 수)에 대해 다음과 같이 정의합니다.

```
current_difficulty(height) = max(1, floor(10000 / 2^(floor(height/10))))
```

즉, 높이 0~9는 10000, 10~19는 5000, 20~29는 2500, … 으로 단계적으로 감소합니다.

## 백엔드 실행(Django)

사전 준비: Python 3.10+ 권장

```
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver 0.0.0.0:8002
```

엔드포인트
- `GET /api/status` — 현재 높이와 난이도
- `GET /api/blocks` — 최신 블록 목록(최대 200개)
- `POST /api/mine` — 채굴 시도 제출(JSON: `{ miner, nonce }`)
- `GET /api/stream` — SSE 스트림(새 블록 및 주기적 상태 방송)

CORS는 간단한 미들웨어(`playground_server/simplecors.py`)로 허용되어, 프론트 개발 서버(5173)에서 접근 가능합니다.

## 프론트엔드 실행(Vue 3 + Vite)

사전 준비: Node.js 18+

```
cd frontend
npm install
# (선택) 백엔드 주소가 다르면 .env 파일에 설정
# VITE_API_BASE=http://127.0.0.1:8002
npm run dev
```

브라우저에서 `http://localhost:5173` 접속 후, 사이드바에서 "비트코인 채굴(간이)"을 선택하세요.

## 사용 방법

1. 우측 패널에서 닉네임을 입력합니다(기본: guest).
2. "채굴 시도하기" 버튼을 누르면 1~100000 사이의 난수가 생성됩니다.
3. 난수 ≤ 현재 난이도(허용 최대값)이면 서버로 제출되어 블록이 생성되고, 성공 메시지를 확인할 수 있습니다.
4. 다른 사용자가 블록을 채굴하면 SSE를 통해 실시간으로 블록 목록과 난이도가 갱신됩니다.

## 참고 사항

- 프론트-백엔드 기본 주소는 `http://127.0.0.1:8002`으로 설정되어 있습니다. 다른 주소를 사용할 경우 `frontend/.env`에 `VITE_API_BASE`를 지정하세요.
- 데이터베이스는 SQLite를 사용합니다. 파일은 `backend/db.sqlite3`로 생성됩니다.
- 보안을 고려하지 않은 데모용 코드입니다. 실제 서비스 전에는 인증/권한, 입력 검증 강화, 내구성 있는 브로드캐스터(예: Redis Pub/Sub) 등을 도입하세요.
- 요구하신 "TCP 서버"를 브라우저가 직접 사용할 수는 없으므로, 현재는 SSE(HTTP)로 구현했습니다. 만약 원하시면 별도의 순수 TCP 서버(예: 관리 커맨드로 `socketserver` 기반)와 백엔드 내부 브리지(예: 큐/브로드캐스터 공유)를 추가해 드릴 수 있습니다.
