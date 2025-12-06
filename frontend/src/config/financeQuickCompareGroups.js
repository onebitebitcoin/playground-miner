export const defaultFinanceQuickCompareGroups = [
  {
    key: 'frequent',
    label: '자주 찾는 종목',
    sort_order: 0,
    contextKey: 'safe_assets',
    assets: [
      '서울 아파트',
      '서울 아파트 (LTV 50%)',
      '금',
      '미국 10년물 국채',
      'S&P 500',
      '코스피',
      '나스닥 100',
      '엔비디아',
      '코카콜라',
      '테슬라',
      '애플',
      '버크셔해서웨이'
    ]
  },
  {
    key: 'us_bigtech',
    label: '미국 빅테크',
    sort_order: 10,
    contextKey: 'us_bigtech',
    assets: ['애플', '엔비디아', '아마존', '메타', '구글', '마이크로소프트', '테슬라']
  },
  {
    key: 'kr_bluechips',
    label: '국내 주요 주식',
    sort_order: 20,
    contextKey: 'kr_equity',
    assets: ['삼성전자', 'SK 하이닉스', 'LG 에너지솔루션', '삼성 바이오로직스', '현대차', 'KB 금융', '카카오', '네이버']
  },
  {
    key: 'dividend_favorites',
    label: '주요 배당주 TOP10',
    sort_order: 99,
    contextKey: 'safe_assets',
    assets: [
      '삼성전자',
      'SK텔레콤',
      'KT&G',
      'KB 금융',
      '신한지주',
      '코카콜라',
      '프록터 앤 갬블',
      '존슨앤존슨',
      '맥도날드',
      'AT&T'
    ]
  }
]
