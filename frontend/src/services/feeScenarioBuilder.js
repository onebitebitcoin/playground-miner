export function buildFeeScenarios({
  amount,
  bitcoinPrice,
  btcTransferFee,
  feeRates,
  withdrawalFees,
  lightningServices,
  lightningServicesInfo,
  exchangeRatesInfo
}) {
  if (!amount || !bitcoinPrice) {
    return []
  }

  const results = []
  const safeFeeRates = feeRates || {}
  const safeWithdrawalFees = withdrawalFees || {}
  const safeLightningServices = lightningServices || {}
  const safeLightningInfo = lightningServicesInfo || {}
  const safeExchangeInfo = exchangeRatesInfo || {}

  const krwFee = (btcAmount = 0) => (btcAmount || 0) * bitcoinPrice

  const getExchangeNote = (key) => (safeExchangeInfo[key]?.is_event ? '한시적 이벤트' : '')
  const getExchangeEventDetails = (key) => safeExchangeInfo[key]?.event_details || ''

  const pushScenario = (scenario) => {
    results.push({
      tradingFee: 0,
      transferFee: 0,
      lightningFee: 0,
      totalFee: 0,
      actualAmount: 0,
      feeRate: 0,
      originalAmount: amount,
      ...scenario
    })
  }

  // 1. 업비트 BTC → 바이낸스 → 온체인 개인지갑
  pushScenario({
    id: 'upbit-btc-binance-onchain',
    title: '업비트 BTC → 바이낸스 → 온체인 개인지갑',
    description: '업비트 비트코인 직접 송금 → 바이낸스 → 온체인 개인지갑 출금',
    exchanges: [
      {
        name: '업비트 (BTC)',
        rate: safeFeeRates.upbit_btc,
        note: getExchangeNote('upbit_btc'),
        eventDetails: getExchangeEventDetails('upbit_btc')
      },
      {
        name: '바이낸스',
        rate: 0,
        note: '',
        eventDetails: ''
      }
    ],
    withdrawalFees: [
      { name: '업비트 BTC 송금', amount: btcTransferFee, amountKrw: krwFee(btcTransferFee) },
      { name: '바이낸스 온체인 개인지갑', amount: safeWithdrawalFees.binance_onchain, amountKrw: krwFee(safeWithdrawalFees.binance_onchain) }
    ],
    tradingFee: amount * (safeFeeRates.upbit_btc / 100),
    transferFee: krwFee(btcTransferFee + safeWithdrawalFees.binance_onchain)
  })

  // 2. 업비트 BTC → OKX → 온체인 개인지갑
  pushScenario({
    id: 'upbit-btc-okx-onchain',
    title: '업비트 BTC → OKX → 온체인 개인지갑',
    description: '업비트 비트코인 직접 송금 → OKX → 온체인 개인지갑 출금',
    exchanges: [
      {
        name: '업비트 (BTC)',
        rate: safeFeeRates.upbit_btc,
        note: getExchangeNote('upbit_btc'),
        eventDetails: getExchangeEventDetails('upbit_btc')
      },
      {
        name: 'OKX',
        rate: 0,
        note: '',
        eventDetails: ''
      }
    ],
    withdrawalFees: [
      { name: '업비트 BTC 송금', amount: btcTransferFee, amountKrw: krwFee(btcTransferFee) },
      { name: 'OKX 온체인 개인지갑', amount: safeWithdrawalFees.okx_onchain, amountKrw: krwFee(safeWithdrawalFees.okx_onchain) }
    ],
    tradingFee: amount * (safeFeeRates.upbit_btc / 100),
    transferFee: krwFee(btcTransferFee + safeWithdrawalFees.okx_onchain)
  })

  // 3. 빗썸 BTC → OKX → 온체인 개인지갑
  pushScenario({
    id: 'bithumb-btc-okx-onchain',
    title: '빗썸 BTC → OKX → 온체인 개인지갑',
    description: '빗썸 비트코인 직접 송금 → OKX → 온체인 개인지갑 출금',
    exchanges: [
      {
        name: '빗썸 (BTC)',
        rate: safeFeeRates.bithumb,
        note: getExchangeNote('bithumb'),
        eventDetails: getExchangeEventDetails('bithumb')
      },
      {
        name: 'OKX',
        rate: 0,
        note: '',
        eventDetails: ''
      }
    ],
    withdrawalFees: [
      { name: '빗썸 BTC 송금', amount: btcTransferFee, amountKrw: krwFee(btcTransferFee) },
      { name: 'OKX 온체인 개인지갑', amount: safeWithdrawalFees.okx_onchain, amountKrw: krwFee(safeWithdrawalFees.okx_onchain) }
    ],
    tradingFee: amount * (safeFeeRates.bithumb / 100),
    transferFee: krwFee(btcTransferFee + safeWithdrawalFees.okx_onchain)
  })

  // 4. 업비트 → OKX → 온체인 개인지갑
  pushScenario({
    id: 'upbit-usdt-okx-onchain',
    title: '업비트 → OKX → 온체인 개인지갑',
    description: '업비트 USDT → OKX 비트코인 매수 → 온체인 개인지갑 출금',
    exchanges: [
      {
        name: '업비트 (USDT)',
        rate: safeFeeRates.upbit_usdt,
        note: getExchangeNote('upbit_usdt'),
        eventDetails: getExchangeEventDetails('upbit_usdt')
      },
      {
        name: 'OKX',
        rate: safeFeeRates.okx,
        note: getExchangeNote('okx'),
        eventDetails: getExchangeEventDetails('okx')
      }
    ],
    withdrawalFees: [
      { name: 'OKX 온체인 개인지갑', amount: safeWithdrawalFees.okx_onchain, amountKrw: krwFee(safeWithdrawalFees.okx_onchain) }
    ],
    tradingFee: amount * (safeFeeRates.upbit_usdt / 100) + amount * (safeFeeRates.okx / 100),
    transferFee: krwFee(safeWithdrawalFees.okx_onchain)
  })

  // 5. 업비트 → 바이낸스 → 온체인 개인지갑
  pushScenario({
    id: 'upbit-usdt-binance-onchain',
    title: '업비트 → 바이낸스 → 온체인 개인지갑',
    description: '업비트 USDT → 바이낸스 비트코인 매수 → 온체인 개인지갑 출금',
    exchanges: [
      {
        name: '업비트 (USDT)',
        rate: safeFeeRates.upbit_usdt,
        note: getExchangeNote('upbit_usdt'),
        eventDetails: getExchangeEventDetails('upbit_usdt')
      },
      {
        name: '바이낸스',
        rate: safeFeeRates.binance,
        note: getExchangeNote('binance'),
        eventDetails: getExchangeEventDetails('binance')
      }
    ],
    withdrawalFees: [
      { name: '바이낸스 온체인 개인지갑', amount: safeWithdrawalFees.binance_onchain, amountKrw: krwFee(safeWithdrawalFees.binance_onchain) }
    ],
    tradingFee: amount * (safeFeeRates.upbit_usdt / 100) + amount * (safeFeeRates.binance / 100),
    transferFee: krwFee(safeWithdrawalFees.binance_onchain)
  })

  // 7. 업비트 BTC → 바이낸스 → Coinos → 온체인 개인지갑
  pushScenario({
    id: 'upbit-btc-binance-lightning-coinos',
    title: '업비트 BTC → 바이낸스 → Coinos → 온체인 개인지갑',
    description: '업비트 비트코인 직접 송금 → 바이낸스 → 라이트닝 → Coinos → 온체인 개인지갑',
    exchanges: [
      {
        name: '업비트 (BTC)',
        rate: safeFeeRates.upbit_btc,
        note: getExchangeNote('upbit_btc'),
        eventDetails: getExchangeEventDetails('upbit_btc')
      }
    ],
    withdrawalFees: [
      { name: '업비트 BTC 송금', amount: btcTransferFee, amountKrw: krwFee(btcTransferFee) },
      { name: '바이낸스 라이트닝', amount: safeWithdrawalFees.binance_lightning, amountKrw: krwFee(safeWithdrawalFees.binance_lightning) }
    ],
    lightningServices: [
      {
        name: 'Coinos',
        rate: safeLightningServices.coinos,
        isKyc: safeLightningInfo.coinos?.is_kyc || false,
        isCustodial: safeLightningInfo.coinos?.is_custodial ?? true
      }
    ],
    tradingFee: amount * (safeFeeRates.upbit_btc / 100),
    transferFee: krwFee(btcTransferFee + safeWithdrawalFees.binance_lightning),
    lightningFee: amount * (safeLightningServices.coinos / 100)
  })

  // 9. 업비트 BTC → OKX → Coinos → 온체인 개인지갑
  pushScenario({
    id: 'upbit-btc-okx-lightning-coinos',
    title: '업비트 BTC → OKX → Coinos → 온체인 개인지갑',
    description: '업비트 비트코인 직접 송금 → OKX → 라이트닝 → Coinos → 온체인 개인지갑',
    exchanges: [
      {
        name: '업비트 (BTC)',
        rate: safeFeeRates.upbit_btc,
        note: getExchangeNote('upbit_btc'),
        eventDetails: getExchangeEventDetails('upbit_btc')
      }
    ],
    withdrawalFees: [
      { name: '업비트 BTC 송금', amount: btcTransferFee, amountKrw: krwFee(btcTransferFee) },
      { name: 'OKX 라이트닝', amount: safeWithdrawalFees.okx_lightning, amountKrw: krwFee(safeWithdrawalFees.okx_lightning) }
    ],
    lightningServices: [
      {
        name: 'Coinos',
        rate: safeLightningServices.coinos,
        isKyc: safeLightningInfo.coinos?.is_kyc || false,
        isCustodial: safeLightningInfo.coinos?.is_custodial ?? true
      }
    ],
    tradingFee: amount * (safeFeeRates.upbit_btc / 100),
    transferFee: krwFee(btcTransferFee + safeWithdrawalFees.okx_lightning),
    lightningFee: amount * (safeLightningServices.coinos / 100)
  })

  // 11. 업비트 → OKX → Coinos → 온체인 개인지갑
  pushScenario({
    id: 'upbit-usdt-okx-lightning-coinos',
    title: '업비트 → OKX → Coinos → 온체인 개인지갑',
    description: '업비트 USDT → OKX → 라이트닝 → Coinos → 온체인 개인지갑',
    exchanges: [
      {
        name: '업비트 (USDT)',
        rate: safeFeeRates.upbit_usdt,
        note: getExchangeNote('upbit_usdt'),
        eventDetails: getExchangeEventDetails('upbit_usdt')
      },
      {
        name: 'OKX',
        rate: safeFeeRates.okx,
        note: getExchangeNote('okx'),
        eventDetails: getExchangeEventDetails('okx')
      }
    ],
    withdrawalFees: [
      { name: 'OKX 라이트닝', amount: safeWithdrawalFees.okx_lightning, amountKrw: krwFee(safeWithdrawalFees.okx_lightning) }
    ],
    lightningServices: [
      {
        name: 'Coinos',
        rate: safeLightningServices.coinos,
        isKyc: safeLightningInfo.coinos?.is_kyc || false,
        isCustodial: safeLightningInfo.coinos?.is_custodial ?? true
      }
    ],
    tradingFee: amount * (safeFeeRates.upbit_usdt / 100) + amount * (safeFeeRates.okx / 100),
    transferFee: krwFee(safeWithdrawalFees.okx_lightning),
    lightningFee: amount * (safeLightningServices.coinos / 100)
  })

  // 13. 업비트 → 바이낸스 → Coinos → 온체인 개인지갑
  pushScenario({
    id: 'upbit-usdt-binance-lightning-coinos',
    title: '업비트 → 바이낸스 → Coinos → 온체인 개인지갑',
    description: '업비트 USDT → 바이낸스 → 라이트닝 → Coinos → 온체인 개인지갑',
    exchanges: [
      {
        name: '업비트 (USDT)',
        rate: safeFeeRates.upbit_usdt,
        note: getExchangeNote('upbit_usdt'),
        eventDetails: getExchangeEventDetails('upbit_usdt')
      },
      {
        name: '바이낸스',
        rate: safeFeeRates.binance,
        note: getExchangeNote('binance'),
        eventDetails: getExchangeEventDetails('binance')
      }
    ],
    withdrawalFees: [
      { name: '바이낸스 라이트닝', amount: safeWithdrawalFees.binance_lightning, amountKrw: krwFee(safeWithdrawalFees.binance_lightning) }
    ],
    lightningServices: [
      {
        name: 'Coinos',
        rate: safeLightningServices.coinos,
        isKyc: safeLightningInfo.coinos?.is_kyc || false,
        isCustodial: safeLightningInfo.coinos?.is_custodial ?? true
      }
    ],
    tradingFee: amount * (safeFeeRates.upbit_usdt / 100) + amount * (safeFeeRates.binance / 100),
    transferFee: krwFee(safeWithdrawalFees.binance_lightning),
    lightningFee: amount * (safeLightningServices.coinos / 100)
  })

  // 업비트 → OKX → Strike → 온체인 개인지갑
  pushScenario({
    id: 'upbit-usdt-okx-lightning-strike',
    title: '업비트 → OKX → Strike → 온체인 개인지갑',
    description: '업비트 USDT → OKX → 라이트닝 → Strike → 온체인 개인지갑',
    exchanges: [
      {
        name: '업비트 (USDT)',
        rate: safeFeeRates.upbit_usdt,
        note: getExchangeNote('upbit_usdt'),
        eventDetails: getExchangeEventDetails('upbit_usdt')
      },
      {
        name: 'OKX',
        rate: safeFeeRates.okx,
        note: getExchangeNote('okx'),
        eventDetails: getExchangeEventDetails('okx')
      }
    ],
    withdrawalFees: [
      { name: 'OKX 라이트닝', amount: safeWithdrawalFees.okx_lightning, amountKrw: krwFee(safeWithdrawalFees.okx_lightning) }
    ],
    lightningServices: [
      {
        name: 'Strike',
        rate: safeLightningServices.strike,
        isKyc: safeLightningInfo.strike?.is_kyc || true,
        isCustodial: safeLightningInfo.strike?.is_custodial ?? true
      }
    ],
    tradingFee: amount * (safeFeeRates.upbit_usdt / 100) + amount * (safeFeeRates.okx / 100),
    transferFee: krwFee(safeWithdrawalFees.okx_lightning),
    lightningFee: amount * (safeLightningServices.strike / 100)
  })

  // 업비트 BTC → OKX → Strike → 온체인 개인지갑
  pushScenario({
    id: 'upbit-btc-okx-lightning-strike',
    title: '업비트 BTC → OKX → Strike → 온체인 개인지갑',
    description: '업비트 비트코인 직접 송금 → OKX → 라이트닝 → Strike → 온체인 개인지갑',
    exchanges: [
      {
        name: '업비트 (BTC)',
        rate: safeFeeRates.upbit_btc,
        note: getExchangeNote('upbit_btc'),
        eventDetails: getExchangeEventDetails('upbit_btc')
      }
    ],
    withdrawalFees: [
      { name: '업비트 BTC 송금', amount: btcTransferFee, amountKrw: krwFee(btcTransferFee) },
      { name: 'OKX 라이트닝', amount: safeWithdrawalFees.okx_lightning, amountKrw: krwFee(safeWithdrawalFees.okx_lightning) }
    ],
    lightningServices: [
      {
        name: 'Strike',
        rate: safeLightningServices.strike,
        isKyc: safeLightningInfo.strike?.is_kyc || true,
        isCustodial: safeLightningInfo.strike?.is_custodial ?? true
      }
    ],
    tradingFee: amount * (safeFeeRates.upbit_btc / 100),
    transferFee: krwFee(btcTransferFee + safeWithdrawalFees.okx_lightning),
    lightningFee: amount * (safeLightningServices.strike / 100)
  })

  results.forEach(result => {
    let currentAmount = amount

    const actualTradingFee = currentAmount * (result.exchanges[0].rate / 100)
    currentAmount -= actualTradingFee

    currentAmount -= result.transferFee

    let secondTradingFee = 0
    if (result.exchanges.length > 1) {
      secondTradingFee = currentAmount * (result.exchanges[1].rate / 100)
      currentAmount -= secondTradingFee
    }

    let actualLightningFee = 0
    if (result.lightningServices && result.lightningServices.length > 0) {
      actualLightningFee = currentAmount * (result.lightningServices[0].rate / 100)
      currentAmount -= actualLightningFee
    }

    result.firstTradingFee = actualTradingFee
    result.secondTradingFee = secondTradingFee
    result.tradingFee = actualTradingFee + secondTradingFee
    result.lightningFee = actualLightningFee
    result.totalFee = result.tradingFee + result.transferFee + result.lightningFee
    result.actualAmount = currentAmount
    result.feeRate = ((result.totalFee / amount) * 100).toFixed(3)

    if (!result.lightningServices || result.lightningServices.length === 0) {
      result.finalTransferType = '온체인'
    } else {
      const svc = (result.lightningServices[0]?.name || '')
      result.finalTransferType = (svc === 'Coinos') ? '온체인' : '라이트닝'
    }

    if (result.lightningServices && result.lightningServices.length > 0 && result.withdrawalFees && result.withdrawalFees.length > 0) {
      const lightningFee = result.withdrawalFees.find(f => f.name && f.name.includes('라이트닝'))
      if (lightningFee && lightningFee.amountKrw > 0) {
        result.lightningArrowFee = { amount: new Intl.NumberFormat('ko-KR').format(Math.round(lightningFee.amountKrw)), btc: lightningFee.amount }
      } else {
        result.lightningArrowFee = null
      }
    } else {
      result.lightningArrowFee = null
    }

    if (result.finalTransferType === '온체인' && result.withdrawalFees && result.withdrawalFees.length > 0) {
      const onchainFee =
        result.withdrawalFees.find(f => f.name && (f.name.includes('온체인') || f.name.includes('개인지갑'))) ||
        result.withdrawalFees.find(f => f.name && f.name.includes('BTC 송금'))
      if (onchainFee && onchainFee.amountKrw > 0) {
        result.finalArrowWithdrawalFee = { amount: new Intl.NumberFormat('ko-KR').format(Math.round(onchainFee.amountKrw)), btc: onchainFee.amount }
      } else {
        result.finalArrowWithdrawalFee = { amount: '0', btc: '0' }
      }
    } else {
      result.finalArrowWithdrawalFee = null
    }
  })

  return results
}
