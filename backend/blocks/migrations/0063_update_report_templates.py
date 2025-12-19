from django.db import migrations


USER_TEMPLATE = """{{SUBJECT_NAME}}의 사주와 비트코인 궁합을 분석하세요.{{SUBJECT_EXTRA}}

**작성 지침 (반드시 준수):**

1. **분량**: 800~1000자. 시스템 프롬프트의 요구(비트코인 커리어·재물·인간관계·전략)를 빠짐없이 반영하고, 문단 사이 공백 없이 촘촘히 작성하세요.

2. **출력 템플릿(순서 고정, 마크다운 엄수)**:
   - ## 프로필 브리핑
     - 일간: …
     - 오행 앵커: …
     - 직업/역할: …
   - ## 커리어 & 재물
     - 불릿 2~3개로 비트코인 커리어와 재물 흐름 서술
   - ## 인간관계
     - 협업/대인관계 리듬과 리스크를 불릿 2개로 정리
   - ## 비트코인 전략 체크리스트
     - 1. …
     - 2. …
     - 3. …

3. **근거 & 어휘**: 저장된 사주·스토리·오행 분포에서 최소 2가지 근거를 명시하고, 한자 대신 풀이형 표현을 사용하세요.

4. **금지 사항**: 인사말, 잡담, “모르겠다” 류 표현, 표 생략, 섹션 누락 금지."""

TARGET_TEMPLATE = """{{SUBJECT_NAME}}의 사주와 비트코인 궁합을 분석하세요.{{SUBJECT_EXTRA}}

**작성 지침 (반드시 준수):**

1. **분량**: 800~1000자. 대상 인물의 커리어·재물·인간관계·전략을 모두 포함하세요.

2. **출력 템플릿(순서 고정, 마크다운 엄수)**:
   - ## 프로필 브리핑
     - 일간: …
     - 오행 앵커: …
     - 직업/역할: …
   - ## 커리어 & 재물
     - 불릿 2~3개
   - ## 인간관계
     - 불릿 2개
   - ## 비트코인 전략 체크리스트
     - 1. …
     - 2. …
     - 3. …

3. **근거 & 어휘**: 프리셋 설명/스토리/사주 요약을 근거로 최소 2개의 구체적 사실을 언급하고, 어렵지 않은 언어로 풀이하세요.

4. **금지 사항**: 인사말, 공백 섹션, "모르겠다" 표현 금지."""

TEAM_TEMPLATE = """{{USER_NAME}}와(과) {{TARGET_NAME}}가 함께 비트코인 투자할 때의 팀 궁합을 분석하세요.{{TEAM_EXTRA}}

**작성 지침 (반드시 준수):**

1. **분량**: 700~950자. 두 사람의 사주 앵커, 투자 습관, 협업 리듬, 전략 포지셔닝을 모두 다루세요.

2. **출력 템플릿(순서 고정, 마크다운 엄수)**:
   - ## 팀 특성 & 호흡
     - 사용자 이름과 비교 대상 이름을 모두 언급하는 불릿 2~3개
   - ## 커리어 & 재물 시너지
     - 불릿 2개, 각 문장에 어느 사람이 어떤 역할을 맡는지 명시
   - ## 인간관계/커뮤니케이션
     - 불릿 2개, 갈등 방지법 포함
   - ## 팀 비트코인 전략 체크리스트
     - 1. 역할 분담 규칙
     - 2. 의사결정 루틴
     - 3. 리스크 통제법

3. **근거**: 각 섹션에서 최소 한 번씩 두 사람의 사주 요약 또는 스토리에서 직접 언급한 특징을 인용하세요.

4. **금지 사항**: 인사말, 모호한 표현, 생략표, 섹션 누락 금지."""


def update_report_templates(apps, schema_editor):
    Template = apps.get_model('blocks', 'CompatibilityReportTemplate')
    templates = {
        'user_vs_bitcoin': USER_TEMPLATE,
        'target_vs_bitcoin': TARGET_TEMPLATE,
        'team_vs_bitcoin': TEAM_TEMPLATE,
    }
    for key, content in templates.items():
        Template.objects.filter(key=key).update(content=content)


class Migration(migrations.Migration):

    dependencies = [
        ('blocks', '0062_compatibilityreporttemplate'),
    ]

    operations = [
        migrations.RunPython(update_report_templates, migrations.RunPython.noop),
    ]
