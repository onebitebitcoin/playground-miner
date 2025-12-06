# 빠른 비교 기능 문제 해결

## 문제 분석 결과

백엔드 API와 데이터베이스는 모두 정상 작동하고 있습니다. 다음 사항들을 확인하고 수정했습니다:

### ✅ 확인된 정상 작동 항목:
1. 백엔드 API 엔드포인트 정상 작동
   - `/api/finance/quick-compare-groups` - 빠른 비교 그룹 목록 조회
   - `/api/finance/custom-asset/resolve` - 자산 정보 해석
2. 데이터베이스에 4개의 빠른 비교 그룹 정상 저장
   - 자주 찾는 종목 (12개 자산)
   - 미국 빅테크 (7개 자산)
   - 국내 주요 주식 (8개 자산)
   - 주요 배당주 TOP10 (10개 자산)
3. CORS 설정 정상
4. CSRF 예외 처리 정상
5. 프론트엔드 개발 서버 실행 중

### 🔧 수정된 사항:
1. 데이터베이스의 `sort_order` 값 수정 (잘못된 순서 수정)
   - us_bigtech: 1 → 10
   - kr_bluechips: 2 → 20

## 문제 해결 방법

### 1단계: 브라우저 새로고침
브라우저에서 **하드 리프레시**를 수행하세요:
- macOS: `Cmd + Shift + R`
- Windows/Linux: `Ctrl + Shift + R`

### 2단계: 브라우저 개발자 도구로 확인
만약 여전히 문제가 발생하면, 다음 단계를 따라주세요:

1. 브라우저 개발자 도구 열기 (F12 또는 Cmd+Option+I)

2. **Console 탭** 확인:
   - JavaScript 에러가 있는지 확인
   - 빨간색 에러 메시지 확인

3. **Network 탭** 확인:
   - "미국 빅테크" 버튼 클릭
   - API 호출 확인:
     - `/api/finance/quick-compare-groups` - 200 OK
     - `/api/finance/custom-asset/resolve` 호출들 - 200 OK
   - 실패한 요청이 있다면 상세 정보 확인

### 3단계: 프론트엔드/백엔드 재시작 (필요시)

백엔드 재시작:
```bash
cd backend
# 기존 프로세스 종료
lsof -ti:8000 | xargs kill -9
# 재시작
python3 manage.py runserver
```

프론트엔드 재시작:
```bash
cd frontend
# Ctrl+C로 종료 후
npm run dev
```

## 예상되는 정상 동작

1. 빠른 비교 버튼 클릭 시:
   - 버튼에 로딩 스피너 표시
   - "비교 종목:" 섹션에 자산들이 표시됨
   - 각 자산에 ×  버튼이 표시됨

2. API 호출 흐름:
   ```
   버튼 클릭 
   → quickCompareLoadingKey 설정 (로딩 시작)
   → /api/finance/custom-asset/resolve API 호출 (각 자산마다)
   → customAssets 배열 업데이트
   → quickCompareLoadingKey 초기화 (로딩 완료)
   → 화면에 자산 표시
   ```

## 디버깅 정보

백엔드 API 테스트:
```bash
# 빠른 비교 그룹 조회
curl http://localhost:8000/api/finance/quick-compare-groups

# 자산 정보 해석 테스트
curl -X POST http://localhost:8000/api/finance/custom-asset/resolve \
  -H "Content-Type: application/json" \
  -d '{"name": "애플"}'
```

데이터베이스 확인:
```bash
cd backend
python3 manage.py shell -c "from blocks.models import FinanceQuickCompareGroup; [print(f'{g.key}: {g.label} ({len(g.assets)} assets)') for g in FinanceQuickCompareGroup.objects.all()]"
```

## 추가 지원이 필요한 경우

위 단계를 수행한 후에도 문제가 지속되면, 다음 정보를 제공해주세요:
1. 브라우저 콘솔의 에러 메시지
2. 네트워크 탭의 실패한 요청 상세 정보
3. 어떤 단계에서 문제가 발생하는지 (로딩 시작 안됨 / 로딩 중 멈춤 / 로딩 완료 후 표시 안됨)
