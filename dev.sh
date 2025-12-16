#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 스크립트 디렉토리로 이동
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}🚀 한입 비트코인 놀이터 개발 서버 시작${NC}"
echo "=================================="

# 기존 프로세스 종료 함수
kill_processes() {
    echo -e "${YELLOW}🔍 기존 프로세스 확인 중...${NC}"
    
    # Node.js (Vite) 프로세스 찾기 및 종료
    NODE_PIDS=$(pgrep -f "vite" 2>/dev/null)
    if [ ! -z "$NODE_PIDS" ]; then
        echo -e "${RED}⚠️  기존 Vite 프로세스 발견, 종료 중...${NC}"
        echo "$NODE_PIDS" | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
    
    # Django runserver 프로세스 찾기 및 종료
    DJANGO_PIDS=$(pgrep -f "manage.py runserver" 2>/dev/null)
    if [ ! -z "$DJANGO_PIDS" ]; then
        echo -e "${RED}⚠️  기존 Django 프로세스 발견, 종료 중...${NC}"
        echo "$DJANGO_PIDS" | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
    
    # 포트 8000, 5173 사용 프로세스 확인 및 종료
    for port in 8000 5173; do
        PID=$(lsof -ti:$port 2>/dev/null)
        if [ ! -z "$PID" ]; then
            echo -e "${RED}⚠️  포트 $port 사용 중인 프로세스 (PID: $PID) 종료 중...${NC}"
            kill -9 $PID 2>/dev/null || true
            sleep 1
        fi
    done
    
    echo -e "${GREEN}✅ 프로세스 정리 완료${NC}"
}

# 의존성 설치 확인 함수
check_dependencies() {
    echo -e "${YELLOW}📦 의존성 확인 중...${NC}"
    
    # Frontend 의존성 확인
    if [ ! -d "frontend/node_modules" ]; then
        echo -e "${YELLOW}🔧 Frontend 의존성 설치 중...${NC}"
        cd frontend
        npm install
        cd ..
    fi
    
    # Backend 가상환경 및 의존성 확인
    echo -e "${YELLOW}🔧 Backend 가상환경 및 의존성 확인 중...${NC}"
    cd backend

    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}🔧 Backend 가상환경 생성 중...${NC}"
        python3 -m venv venv
    fi

    # 가상환경 활성화 후 의존성 설치
    source venv/bin/activate
    pip install -r requirements.txt > /dev/null 2>&1
    cd ..
    
    echo -e "${GREEN}✅ 의존성 확인 완료${NC}"
}

# 에러 처리 함수
handle_error() {
    echo -e "${RED}❌ 오류 발생: $1${NC}"
    exit 1
}

# 메인 실행 부분
main() {
    # 기존 프로세스 종료
    kill_processes
    
    # 의존성 확인
    check_dependencies
    
    # 백그라운드에서 Django 서버 실행
    echo -e "${BLUE}🐍 Django 백엔드 서버 시작 중... (포트: 8000)${NC}"
    cd backend
    
    # 가상환경 활성화 후 Django 서버 실행
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate

        # Django 마이그레이션 실행
        echo -e "${YELLOW}📊 데이터베이스 마이그레이션 중...${NC}"
        python3 manage.py migrate --run-syncdb >/dev/null 2>&1 || true

        # Django 서버 백그라운드 실행
        # nohup python3 manage.py runserver 0.0.0.0:8000 > ../backend.log 2>&1 &
        nohup uvicorn playground_server.asgi:application --host 0.0.0.0 --port 8000 --reload > ../backend.log 2>&1 &
    else
        echo -e "${RED}❌ 가상환경을 찾을 수 없습니다.${NC}"
        exit 1
    fi
    BACKEND_PID=$!
    cd ..
    
    # 잠시 대기 (백엔드 서버가 시작될 시간을 줌)
    sleep 3
    
    # 백엔드 서버 상태 확인
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        handle_error "Django 백엔드 서버 시작 실패"
    fi
    
    echo -e "${GREEN}✅ Django 백엔드 서버 시작 완료 (PID: $BACKEND_PID)${NC}"
    
    # Frontend 서버 실행 (포그라운드)
    echo -e "${BLUE}⚡ Vite 프론트엔드 서버 시작 중... (포트: 5173)${NC}"
    echo -e "${GREEN}🌍 프론트엔드: http://localhost:5173${NC}"
    echo -e "${GREEN}🔧 백엔드 API: http://localhost:8000${NC}"
    echo ""
    echo -e "${YELLOW}📝 백엔드 로그는 backend.log 파일에서 확인할 수 있습니다.${NC}"
    echo -e "${YELLOW}🛑 종료하려면 Ctrl+C를 누르세요.${NC}"
    echo "=================================="
    echo ""
    
    cd frontend
    
    # Cleanup function for graceful shutdown
    cleanup() {
        echo ""
        echo -e "${YELLOW}🛑 서버 종료 중...${NC}"
        
        # 백엔드 프로세스 종료
        if [ ! -z "$BACKEND_PID" ] && kill -0 $BACKEND_PID 2>/dev/null; then
            echo -e "${RED}⚠️  Django 백엔드 서버 종료 중...${NC}"
            kill $BACKEND_PID 2>/dev/null || true
        fi
        
        # 추가로 포트 기반 프로세스 종료
        for port in 8000 5173; do
            PID=$(lsof -ti:$port 2>/dev/null)
            if [ ! -z "$PID" ]; then
                kill -9 $PID 2>/dev/null || true
            fi
        done
        
        echo -e "${GREEN}✅ 모든 서버가 종료되었습니다.${NC}"
        exit 0
    }
    
    # Trap signals for cleanup
    trap cleanup SIGINT SIGTERM
    
    # Vite 개발 서버 실행 (포그라운드)
    npm run dev
}

# 스크립트 실행
main "$@"