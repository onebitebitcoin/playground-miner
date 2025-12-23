export const ELEMENTS = [
  { key: 'wood', label: '목(木)', summary: '추진력과 생명력', color: '#22c55e' },
  { key: 'fire', label: '화(火)', summary: '열정과 폭발성', color: '#ef4444' },
  { key: 'earth', label: '토(土)', summary: '안정성과 중재', color: '#d97706' },
  { key: 'metal', label: '금(金)', summary: '냉철함과 결단력', color: '#f59e0b' },
  { key: 'water', label: '수(水)', summary: '유연함과 통찰', color: '#3b82f6' }
]

export function calculateSajuElement(year, month, day) {
  // Simple deterministic algorithm for demo purposes
  const hash = (year * 31 + month * 13 + day) % ELEMENTS.length
  return {
    element: ELEMENTS[hash],
    hash
  }
}

export function calculateZodiacSign(year) {
  const animals = ['쥐', '소', '호랑이', '토끼', '용', '뱀', '말', '양', '원숭이', '닭', '개', '돼지']
  return animals[(year - 4) % 12]
}

export function calculateYinYang(year, month, day) {
  return (year + month + day) % 2 === 0 ? '양(陽)' : '음(陰)'
}

export function buildRadarChartData(elementRatios, { size = 200, maxRadius = 80, activeKey = null } = {}) {
  const center = size / 2
  const angleStep = (Math.PI * 2) / 5
  
  const axes = ELEMENTS.map((el, i) => {
    const angle = i * angleStep - Math.PI / 2
    return {
      key: el.key,
      label: el.label,
      x2: center + Math.cos(angle) * maxRadius,
      y2: center + Math.sin(angle) * maxRadius,
      labelX: center + Math.cos(angle) * (maxRadius + 20),
      labelY: center + Math.sin(angle) * (maxRadius + 20)
    }
  })

  const markers = ELEMENTS.map((el, i) => {
    const angle = i * angleStep - Math.PI / 2
    const ratio = elementRatios[el.key] || 20
    const radius = (ratio / 100) * maxRadius
    return {
      key: el.key,
      label: el.label,
      ratio,
      x: center + Math.cos(angle) * radius,
      y: center + Math.sin(angle) * radius,
      active: el.key === activeKey
    }
  })

  const polygonPoints = markers.map(m => `${m.x},${m.y}`).join(' ')

  return {
    size,
    center,
    maxRadius,
    axes,
    markers,
    polygonPoints
  }
}
