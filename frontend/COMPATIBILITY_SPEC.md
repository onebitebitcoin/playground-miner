# Bitcoin Compatibility Service Spec

## Overview
- Route: `/compatibility` (`name: 'compatibility'`).
- Sidebar toggle key: `show_compatibility` (defaults to `true`). Admins can enable/disable via Admin → Settings → Sidebar menu configuration.
- Component entry point: `src/pages/CompatibilityPage.vue`.
- Primary goals:
  1. Show Bitcoin's assumed 사주적 속성 (금 70% / 화 30%) as baseline.
  2. Collect user 생년월일 (required) + optional 태어난 시간.
  3. Simulate a multi-agent pipeline (same feeling as Finance page) with logs and stage cards.
  4. Output a compatibility report (score, rating, 전략, 오행 요약, 시간대별 조언, 리스크 노트).

## UI Structure (`CompatibilityPage.vue`)
1. **Bitcoin Highlights section**
   - `bitcoinHighlights` array renders cards (천간/지지, 사이클 기준 등).
   - Accent palette limited to grayscale + orange accent to stay within “≤3 colors” constraint.
2. **User Input + Report (left column on desktop)**
   - Date input (`birthdate`, required). Browser-native date picker.
   - Time input (`birthtime`, optional). Disabled if `timeUnknown` checkbox checked.
   - CTA triggers `handleCompatibility()`.
   - Report area shows summary cards once `compatibilityResult` exists; otherwise dashed placeholder.
3. **Agent Log + Stage Tracker (right column)**
   - Stage cards bound to `stageStatuses` computed from `AGENT_STAGES`, `activeStage`, and `completedStageKeys`.
   - Reuses `AdminPromptPanel` for actual log console (`showLogs` toggled, default `true`).

## State & Logic
- Reactive state declared inside `<script setup>`: `birthdate`, `birthtime`, `timeUnknown`, `loading`, `errorMessage`, etc.
- `handleCompatibility()` flow:
  1. Validate `birthdate` (shows inline error if missing).
  2. Reset previous pipeline via `resetPipeline()` (clears logs and stage trackers).
  3. Capture `runId` (`Date.now()`) to guard against overlapping runs. Stored in `currentRunId`.
  4. Iterate through `AGENT_STAGES`. For each stage: set `activeStage`, push log stub, wait `400~800ms`, then mark stage as completed. Early exit if `currentRunId` changes (user restarted flow).
  5. After stage loop, call `buildCompatibility(payload)` to assemble final data. Push success log and set `compatibilityResult`.
  6. Reset `activeStage` and `loading`.
- `displayLogs` computed simply proxies `logs` for `AdminPromptPanel`.

### Compatibility Engine Details
- `normalizePayload()` splits `birthdate` => `year/month/day` numbers, attaches `time` (or `null` if unknown).
- `ELEMENTS`: array of 5 base 오행 definitions (label + summary).
- `ZODIAC_SIGNS`: 12 띠 names used via `payload.year % 12`.
- `AGENT_STAGES`: 4 stage descriptors with `key`, `label`, `description`, and sample log text (mirrors Finance page terminology so UX feels consistent).
- `STRATEGY_LIBRARY`: maps 각 오행 → 추천 전략 (style/focus/allocation text).
- `TIME_WINDOWS`: 5 buckets (dawn/morning/afternoon/evening/unknown) with score bonuses and coaching copy.
- `ELEMENT_AFFINITY`: currently hard-coded for Bitcoin의 금(金) 중심 기운 (`allies: earth/water`, `neutral: metal/wood`, `challenges: fire`).
- `buildCompatibility(payload)` steps:
  1. Deterministic element pick: `(year + month + day) % ELEMENTS.length`.
  2. Base score = `58 + (month % 7)`.
  3. Adjust based on affinity (+18 allies / +8 neutral / -12 challenge).
  4. Add `timeAdvice.bonus`, add parity tweak (`day % 2 === 0 ? +3 : -1`). Clamp to `[35, 98]`.
  5. Map to rating string (찰떡궁합 / 균형 잡힌 합 / 중립형 합 / 주의가 필요한 합).
  6. Compose narrative and risk memo using helper dictionaries.
- `deriveTimeAdvice(time)` maps HH:mm to `TIME_WINDOWS` bucket; `'unknown'` if time empty or checkbox checked.

## Logs & Stage Tracker
- `logs` array holds strings. Each stage pushes its own `log` text; final stage pushes `[완료] …` message summarizing 추천 전략.
- `AdminPromptPanel` consumes `displayLogs` and `showLogs` to display interactive log drawer identical to Finance page component.
- Stage cards rely on `stageStatuses` computed to label each stage as pending/active/done and adjust icon color/animation accordingly.

## Sidebar / Routing Integration
- `router/index.js` imports and mounts `CompatibilityPage` at `/compatibility`.
- `App.vue` sidebar config now includes `show_compatibility`. Menu items and mobile tabs automatically include “궁합” if the flag is `true`.
- Admin settings (`AdminSettingsTab.vue`) exposes the toggle and merges backend config onto defaults to preserve new key.
- `apiGetSidebarConfig` consumers (App + Admin settings) merge existing defaults with remote config so missing keys still fallback to `true/false` defaults.

## Future Work Ideas (for Claude or others)
1. **Real Backend Hook**: Replace `buildCompatibility()` mock logic with API call (streaming logs, SSE, etc.). Keep `currentRunId` guard to avoid stale responses.
2. **Time Zone Handling**: If backend requires locale-aware birth times, extend payload with timezone or location selectors.
3. **Additional Agent Stages**: Expand `AGENT_STAGES` to include actual sub-agents (예: 온체인 데이터, 심리 분석) and update `stageStatuses` accordingly.
4. **Result Visualization**: Add radar chart comparing Bitcoin vs. user 오행 분포; leverage same color palette.
5. **Persistence**: Cache last-used birth info (localStorage) with explicit user consent.

Use this spec if the task is interrupted so another agent (e.g., Claude) can continue implementing deeper logic or backend connections without reverse-engineering the UI.
