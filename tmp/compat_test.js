const ELEMENTS = [
  { key: 'wood', label: '목(木)', summary: '확장과 성장, 트렌드 파악에 빠름' },
  { key: 'fire', label: '화(火)', summary: '추진력과 속도, 모멘텀 집중' },
  { key: 'earth', label: '토(土)', summary: '안정과 조율, 리스크 관리 탁월' },
  { key: 'metal', label: '금(金)', summary: '정교함과 구조화, 규칙 기반 판단' },
  { key: 'water', label: '수(水)', summary: '흐름과 적응, 변동성 흡수' }
]
const ZODIAC_SIGNS = ['자(쥐)', '축(소)', '인(호랑이)', '묘(토끼)', '진(용)', '사(뱀)', '오(말)', '미(양)', '신(원숭이)', '유(닭)', '술(개)', '해(돼지)']
const ELEMENT_AFFINITY = {
  metal: { allies: ['earth', 'water'], neutral: ['metal', 'wood'], challenges: ['fire'] }
}
const STRATEGY_LIBRARY = {
  wood: { style: '성장형 장기 적립', focus: '...', allocation: '...' },
  fire: { style: '열정적 정기 저축', focus: '...', allocation: '...' },
  earth: { style: '안정형 장기 축적', focus: '...', allocation: '...' },
  metal: { style: '규율형 정기 저축', focus: '...', allocation: '...' },
  water: { style: '유연형 꾸준한 축적', focus: '...', allocation: '...' }
}
const TIME_WINDOWS = [
  { key: 'dawn', bonus: 6 },
  { key: 'morning', bonus: 4 },
  { key: 'afternoon', bonus: 2 },
  { key: 'evening', bonus: 5 },
  { key: 'unknown', bonus: 0 }
]
function calculateZodiacSign(year, month, day){
  let zy = year
  if (month === 1 || (month === 2 && day <=3)) zy = year-1
  const idx = (zy - 4) % 12
  return ZODIAC_SIGNS[idx>=0?idx:idx+12]
}
function calculateYinYang(year, month, day){
  let zy = year
  if (month === 1 || (month ===2 && day<=3)) zy = year-1
  return zy % 2 === 0 ? '양':'음'
}
function deriveTimeAdvice(){ return TIME_WINDOWS[4] }
function build(payload){
  const element = ELEMENTS[(payload.year + payload.month + payload.day) % ELEMENTS.length]
  const zodiac = calculateZodiacSign(payload.year, payload.month, payload.day)
  const yinYang = calculateYinYang(payload.year, payload.month, payload.day)
  let score = 58 + (payload.month % 7)
  const affinity = ELEMENT_AFFINITY.metal
  if (affinity.allies.includes(element.key)) score += 18
  else if (affinity.neutral.includes(element.key)) score += 8
  else if (affinity.challenges.includes(element.key)) score -= 12
  const timeAdvice = deriveTimeAdvice(null)
  score += timeAdvice.bonus
  score += payload.day % 2 === 0 ? 3 : -1
  score = Math.max(35, Math.min(98, Math.round(score)))
  const rating = score >= 85 ? '찰떡궁합' : score >= 70 ? '균형 잡힌 합' : score >= 55 ? '중립형 합' : '주의가 필요한 합'
  const strategy = STRATEGY_LIBRARY[element.key]
  return { element: element.label, zodiac, yinYang, score, rating, strategy: strategy.style }
}
const inputs = [
  {name:'saylor',birth:'1965-02-04'},
  {name:'trump',birth:'1946-06-14'},
  {name:'fink',birth:'1952-11-02'},
  {name:'dimon',birth:'1956-03-13'}
]
for(const input of inputs){
  const [year,month,day] = input.birth.split('-').map(Number)
  const res = build({year,month,day})
  console.log(input.name,res)
}
