#!/bin/bash
echo "================================================"
echo "궁합 페이지 로그 모니터링 시작"
echo "================================================"
echo ""
echo "Ctrl+C를 눌러 종료하세요"
echo ""

# Clear previous log file
> /tmp/compatibility_logs.txt

# Monitor the logs
tail -f /tmp/claude/tasks/*.output 2>/dev/null | grep --line-buffered "궁합\|Compatibility\|process-saju" | tee -a /tmp/compatibility_logs.txt
