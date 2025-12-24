<template>
  <div class="flex flex-col items-center justify-center select-none">
    <div class="scene" :class="stateClass">
      <div class="grid-pattern"></div>

      <!-- Enhanced pulse rings with glow -->
      <div
        v-for="ring in 5"
        :key="`ring-${ring}`"
        :class="['pulse-ring', `ring-${ring}`, { active: currentState !== 'idle' }]"
      ></div>

      <!-- More data streams -->
      <div
        v-for="stream in 8"
        :key="`stream-${stream}`"
        :class="['data-stream', `stream-${stream}`]"
      ></div>

      <!-- Enhanced sparks -->
      <div
        v-for="spark in 12"
        :key="`spark-${spark}`"
        :class="['spark', `spark-${spark}`, { active: currentState === 'mining' || currentState === 'success' }]"
      ></div>

      <!-- Energy particles -->
      <div
        v-for="particle in 20"
        :key="`particle-${particle}`"
        :class="['energy-particle', `particle-${particle}`, { active: currentState === 'mining' }]"
      ></div>

      <!-- Success explosion particles -->
      <div
        v-for="explosion in 16"
        :key="`explosion-${explosion}`"
        :class="['explosion-particle', `explosion-${explosion}`, { active: currentState === 'success' }]"
      ></div>

      <!-- Rotating energy ring -->
      <div :class="['energy-ring', { active: currentState === 'mining' }]"></div>

      <!-- Coin with enhanced effects -->
      <div class="coin">
        <div class="coin-glow"></div>
        <span>₿</span>
      </div>

      <!-- Pickaxe -->
      <div class="pickaxe">
        <svg viewBox="0 0 100 120" fill="none" xmlns="http://www.w3.org/2000/svg">
          <!-- Handle -->
          <rect x="44" y="25" width="12" height="90" rx="6" fill="#8B4513" />
          <rect x="44" y="25" width="12" height="90" rx="6" fill="url(#woodGradient)" />

          <!-- Metal head -->
          <path d="M20 15 L50 30 L50 45 L20 35 Z" fill="#4A5568" />
          <path d="M80 15 L50 30 L50 45 L80 35 Z" fill="#4A5568" />
          <path d="M20 15 L50 30 L50 45 L20 35 Z" fill="url(#metalGradient1)" />
          <path d="M80 15 L50 30 L50 45 L80 35 Z" fill="url(#metalGradient2)" />

          <!-- Sharp edge -->
          <path d="M15 20 L20 15 L20 35 L15 30 Z" fill="#2D3748" />
          <path d="M85 20 L80 15 L80 35 L85 30 Z" fill="#2D3748" />

          <!-- Highlights -->
          <ellipse cx="25" cy="22" rx="8" ry="3" fill="rgba(255,255,255,0.3)" />
          <ellipse cx="75" cy="22" rx="8" ry="3" fill="rgba(255,255,255,0.3)" />

          <defs>
            <linearGradient id="woodGradient" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stop-color="#A0522D" />
              <stop offset="50%" stop-color="#8B4513" />
              <stop offset="100%" stop-color="#654321" />
            </linearGradient>
            <linearGradient id="metalGradient1" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#718096" />
              <stop offset="50%" stop-color="#4A5568" />
              <stop offset="100%" stop-color="#2D3748" />
            </linearGradient>
            <linearGradient id="metalGradient2" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#718096" />
              <stop offset="50%" stop-color="#4A5568" />
              <stop offset="100%" stop-color="#2D3748" />
            </linearGradient>
          </defs>
        </svg>
      </div>

      <!-- Lightning effects -->
      <div
        v-for="lightning in 4"
        :key="`lightning-${lightning}`"
        :class="['lightning', `lightning-${lightning}`, { active: currentState === 'success' }]"
      ></div>
    </div>
    <div class="status-text mt-3 text-sm text-slate-600 text-center font-medium">
      <span v-if="currentState === 'idle'">대기 중 · 곧 채굴을 시작합니다</span>
      <span v-else-if="currentState === 'mining'" class="mining-text">채굴 중 · 에너지가 집중되고 있습니다!</span>
      <span v-else-if="currentState === 'success'" class="success-text">성공! 새 블록이 생성되었습니다</span>
      <span v-else-if="currentState === 'fail'" class="text-amber-600">실패! 다시 시도해 주세요</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps({
  state: { type: String, default: 'idle' }
})

const allowedStates = ['idle', 'mining', 'success', 'fail']
const currentState = computed(() => (allowedStates.includes(props.state) ? props.state : 'idle'))
const stateClass = computed(() => `state-${currentState.value}`)
</script>

<style scoped>
.scene {
  position: relative;
  width: 13rem;
  height: 13rem;
  border-radius: 1.75rem;
  background: radial-gradient(circle at top, rgba(148, 163, 184, 0.35), rgba(15, 23, 42, 0.95));
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.3);
  box-shadow: 0 25px 60px rgba(15, 23, 42, 0.35);
  transition: all 0.3s ease;
}

.scene.state-mining {
  background: radial-gradient(circle at center, rgba(251, 191, 36, 0.15), rgba(15, 23, 42, 0.95));
  box-shadow: 0 25px 60px rgba(251, 191, 36, 0.25), 0 0 40px rgba(251, 191, 36, 0.15);
  border-color: rgba(251, 191, 36, 0.3);
}

.scene.state-success {
  background: radial-gradient(circle at center, rgba(16, 185, 129, 0.2), rgba(15, 23, 42, 0.95));
  box-shadow: 0 25px 60px rgba(16, 185, 129, 0.35), 0 0 60px rgba(16, 185, 129, 0.25);
  border-color: rgba(16, 185, 129, 0.4);
}

.grid-pattern {
  position: absolute;
  inset: 0;
  background-image: linear-gradient(rgba(255, 255, 255, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.08) 1px, transparent 1px);
  background-size: 24px 24px;
  opacity: 0.4;
  animation: gridShift 12s linear infinite;
}

.pulse-ring {
  position: absolute;
  inset: 20%;
  border: 2px solid rgba(251, 191, 36, 0.5);
  border-radius: 999px;
  opacity: 0;
  box-shadow: 0 0 20px rgba(251, 191, 36, 0.3);
}

.pulse-ring.active {
  animation: pulseRing 2.2s ease-out infinite;
}

.pulse-ring.ring-2 { animation-delay: 0.3s; inset: 15%; }
.pulse-ring.ring-3 { animation-delay: 0.6s; inset: 25%; }
.pulse-ring.ring-4 { animation-delay: 0.9s; inset: 10%; }
.pulse-ring.ring-5 { animation-delay: 1.2s; inset: 30%; }

.data-stream {
  position: absolute;
  width: 3px;
  height: 50px;
  background: linear-gradient(180deg,
    rgba(251, 191, 36, 0) 0%,
    rgba(251, 191, 36, 0.8) 50%,
    rgba(251, 191, 36, 0) 100%);
  border-radius: 999px;
  animation: streamFlow 1s linear infinite;
  box-shadow: 0 0 8px rgba(251, 191, 36, 0.6);
}

.data-stream.stream-1 { left: 15%; top: 10%; animation-delay: 0s; }
.data-stream.stream-2 { left: 35%; top: 5%; animation-delay: 0.15s; }
.data-stream.stream-3 { left: 55%; top: 15%; animation-delay: 0.3s; }
.data-stream.stream-4 { left: 75%; top: 8%; animation-delay: 0.45s; }
.data-stream.stream-5 { left: 25%; top: 20%; animation-delay: 0.6s; }
.data-stream.stream-6 { left: 65%; top: 25%; animation-delay: 0.75s; }
.data-stream.stream-7 { left: 45%; top: 12%; animation-delay: 0.9s; }
.data-stream.stream-8 { left: 85%; top: 18%; animation-delay: 1.05s; }

.coin {
  position: absolute;
  inset: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, #fcd34d, #f59e0b, #d97706);
  display: grid;
  place-items: center;
  font-size: 3.5rem;
  color: #78350f;
  font-weight: 800;
  text-shadow: 0 4px 10px rgba(15, 23, 42, 0.4);
  box-shadow:
    0 15px 30px rgba(251, 191, 36, 0.4),
    inset 0 -6px 12px rgba(120, 53, 15, 0.35),
    0 0 30px rgba(251, 191, 36, 0.3);
  transform: rotateX(15deg);
  z-index: 10;
}

.coin-glow {
  position: absolute;
  inset: -10px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(251, 191, 36, 0.4), transparent 70%);
  opacity: 0;
  animation: glowPulse 2s ease-in-out infinite;
}

.pickaxe {
  position: absolute;
  width: 90px;
  height: 120px;
  left: 50%;
  top: -6%;
  transform-origin: bottom right;
  transform: rotate(-20deg);
  filter: drop-shadow(0 12px 18px rgba(15, 23, 42, 0.7));
  z-index: 20;
}

.scene.state-mining .coin {
  animation: coinPulse 0.8s ease-in-out infinite;
  box-shadow:
    0 15px 30px rgba(251, 191, 36, 0.6),
    inset 0 -6px 12px rgba(120, 53, 15, 0.35),
    0 0 40px rgba(251, 191, 36, 0.5);
}

.scene.state-mining .coin-glow {
  opacity: 1;
}

.scene.state-success .coin {
  animation: coinCelebrate 0.8s ease-out both;
  box-shadow:
    0 20px 40px rgba(16, 185, 129, 0.6),
    inset 0 -6px 12px rgba(120, 53, 15, 0.35),
    0 0 60px rgba(16, 185, 129, 0.6);
}

.scene.state-mining .pickaxe {
  animation: pickaxeSwing 0.6s ease-in-out infinite;
}

.scene.state-success .pickaxe {
  animation: pickaxeFinish 0.8s ease-out forwards;
}

.spark {
  position: absolute;
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: radial-gradient(circle, #fcd34d, #f59e0b);
  opacity: 0;
  box-shadow: 0 0 10px rgba(251, 191, 36, 0.8);
}

.spark.active {
  animation: sparkBurst 0.8s ease-out infinite;
}

.spark.spark-1 { left: 30%; top: 55%; animation-delay: 0s; }
.spark.spark-2 { left: 70%; top: 45%; animation-delay: 0.1s; }
.spark.spark-3 { left: 40%; top: 30%; animation-delay: 0.2s; }
.spark.spark-4 { left: 55%; top: 65%; animation-delay: 0.3s; }
.spark.spark-5 { left: 25%; top: 35%; animation-delay: 0.4s; }
.spark.spark-6 { left: 62%; top: 25%; animation-delay: 0.5s; }
.spark.spark-7 { left: 80%; top: 50%; animation-delay: 0.6s; }
.spark.spark-8 { left: 35%; top: 70%; animation-delay: 0.7s; }
.spark.spark-9 { left: 50%; top: 20%; animation-delay: 0.8s; }
.spark.spark-10 { left: 15%; top: 60%; animation-delay: 0.9s; }
.spark.spark-11 { left: 65%; top: 75%; animation-delay: 1s; }
.spark.spark-12 { left: 45%; top: 40%; animation-delay: 1.1s; }

.energy-particle {
  position: absolute;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: radial-gradient(circle, #fbbf24, #f59e0b);
  opacity: 0;
  box-shadow: 0 0 8px rgba(251, 191, 36, 0.8);
}

.energy-particle.active {
  animation: particleFloat 2s ease-in-out infinite;
}

.energy-particle.particle-1 { left: 10%; top: 80%; animation-delay: 0s; }
.energy-particle.particle-2 { left: 20%; top: 85%; animation-delay: 0.1s; }
.energy-particle.particle-3 { left: 30%; top: 82%; animation-delay: 0.2s; }
.energy-particle.particle-4 { left: 40%; top: 88%; animation-delay: 0.3s; }
.energy-particle.particle-5 { left: 50%; top: 85%; animation-delay: 0.4s; }
.energy-particle.particle-6 { left: 60%; top: 90%; animation-delay: 0.5s; }
.energy-particle.particle-7 { left: 70%; top: 83%; animation-delay: 0.6s; }
.energy-particle.particle-8 { left: 80%; top: 87%; animation-delay: 0.7s; }
.energy-particle.particle-9 { left: 90%; top: 85%; animation-delay: 0.8s; }
.energy-particle.particle-10 { left: 15%; top: 78%; animation-delay: 0.9s; }
.energy-particle.particle-11 { left: 25%; top: 92%; animation-delay: 1s; }
.energy-particle.particle-12 { left: 35%; top: 87%; animation-delay: 1.1s; }
.energy-particle.particle-13 { left: 45%; top: 83%; animation-delay: 1.2s; }
.energy-particle.particle-14 { left: 55%; top: 89%; animation-delay: 1.3s; }
.energy-particle.particle-15 { left: 65%; top: 86%; animation-delay: 1.4s; }
.energy-particle.particle-16 { left: 75%; top: 91%; animation-delay: 1.5s; }
.energy-particle.particle-17 { left: 85%; top: 84%; animation-delay: 1.6s; }
.energy-particle.particle-18 { left: 95%; top: 88%; animation-delay: 1.7s; }
.energy-particle.particle-19 { left: 12%; top: 81%; animation-delay: 1.8s; }
.energy-particle.particle-20 { left: 88%; top: 79%; animation-delay: 1.9s; }

.explosion-particle {
  position: absolute;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: radial-gradient(circle, #10b981, #059669);
  opacity: 0;
  left: 50%;
  top: 50%;
  box-shadow: 0 0 12px rgba(16, 185, 129, 0.8);
}

.explosion-particle.active {
  animation: explode 0.8s ease-out forwards;
}

.explosion-particle.explosion-1 { animation-delay: 0s; --angle: 0deg; }
.explosion-particle.explosion-2 { animation-delay: 0.05s; --angle: 22.5deg; }
.explosion-particle.explosion-3 { animation-delay: 0.1s; --angle: 45deg; }
.explosion-particle.explosion-4 { animation-delay: 0.15s; --angle: 67.5deg; }
.explosion-particle.explosion-5 { animation-delay: 0.2s; --angle: 90deg; }
.explosion-particle.explosion-6 { animation-delay: 0.25s; --angle: 112.5deg; }
.explosion-particle.explosion-7 { animation-delay: 0.3s; --angle: 135deg; }
.explosion-particle.explosion-8 { animation-delay: 0.35s; --angle: 157.5deg; }
.explosion-particle.explosion-9 { animation-delay: 0.4s; --angle: 180deg; }
.explosion-particle.explosion-10 { animation-delay: 0.45s; --angle: 202.5deg; }
.explosion-particle.explosion-11 { animation-delay: 0.5s; --angle: 225deg; }
.explosion-particle.explosion-12 { animation-delay: 0.55s; --angle: 247.5deg; }
.explosion-particle.explosion-13 { animation-delay: 0.6s; --angle: 270deg; }
.explosion-particle.explosion-14 { animation-delay: 0.65s; --angle: 292.5deg; }
.explosion-particle.explosion-15 { animation-delay: 0.7s; --angle: 315deg; }
.explosion-particle.explosion-16 { animation-delay: 0.75s; --angle: 337.5deg; }

.energy-ring {
  position: absolute;
  inset: 30%;
  border: 3px solid rgba(251, 191, 36, 0.6);
  border-radius: 50%;
  opacity: 0;
  box-shadow:
    0 0 20px rgba(251, 191, 36, 0.6),
    inset 0 0 20px rgba(251, 191, 36, 0.3);
}

.energy-ring.active {
  opacity: 1;
  animation: rotateRing 3s linear infinite;
}

.lightning {
  position: absolute;
  width: 4px;
  height: 60px;
  background: linear-gradient(180deg,
    rgba(16, 185, 129, 0) 0%,
    rgba(16, 185, 129, 1) 30%,
    rgba(16, 185, 129, 1) 70%,
    rgba(16, 185, 129, 0) 100%);
  opacity: 0;
  box-shadow: 0 0 20px rgba(16, 185, 129, 0.8);
  filter: blur(1px);
}

.lightning.active {
  animation: lightningStrike 0.4s ease-out;
}

.lightning.lightning-1 { left: 30%; top: -10%; transform: rotate(10deg); animation-delay: 0s; }
.lightning.lightning-2 { left: 70%; top: -10%; transform: rotate(-10deg); animation-delay: 0.1s; }
.lightning.lightning-3 { left: 50%; top: -10%; transform: rotate(-5deg); animation-delay: 0.2s; }
.lightning.lightning-4 { left: 45%; top: -10%; transform: rotate(15deg); animation-delay: 0.3s; }

.scene.state-fail {
  filter: grayscale(0.2);
  background: radial-gradient(circle at top, rgba(248, 250, 252, 0.2), rgba(30, 41, 59, 0.95));
}

.status-text span {
  display: inline-block;
}

.mining-text {
  background: linear-gradient(90deg, #f59e0b, #fbbf24, #f59e0b);
  background-size: 200% auto;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: shimmer 2s linear infinite;
  font-weight: 600;
}

.success-text {
  color: #10b981;
  font-weight: 700;
  animation: successPulse 0.5s ease-out;
  text-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
}

@keyframes gridShift {
  0% { transform: translateY(0); }
  100% { transform: translateY(-24px); }
}

@keyframes pulseRing {
  0% {
    transform: scale(0.7);
    opacity: 0.8;
  }
  100% {
    transform: scale(1.5);
    opacity: 0;
  }
}

@keyframes streamFlow {
  0% {
    transform: translateY(-15px);
    opacity: 0;
  }
  30% {
    opacity: 1;
  }
  100% {
    transform: translateY(60px);
    opacity: 0;
  }
}

@keyframes coinPulse {
  0%, 100% {
    transform: scale(1) rotateX(15deg) rotateY(0deg);
  }
  50% {
    transform: scale(1.06) rotateX(10deg) rotateY(5deg);
  }
}

@keyframes coinCelebrate {
  0% {
    transform: translateY(0) scale(1) rotate(0deg);
  }
  30% {
    transform: translateY(-20px) scale(1.15) rotate(180deg);
  }
  60% {
    transform: translateY(-10px) scale(1.1) rotate(360deg);
  }
  100% {
    transform: translateY(0) scale(1) rotate(360deg);
  }
}

@keyframes pickaxeSwing {
  0%, 100% {
    transform: rotate(-40deg);
  }
  50% {
    transform: rotate(20deg);
  }
}

@keyframes pickaxeFinish {
  0% {
    transform: rotate(-30deg);
  }
  100% {
    transform: rotate(-5deg);
  }
}

@keyframes sparkBurst {
  0% {
    transform: scale(0.3) translate(0, 0);
    opacity: 0;
  }
  30% {
    opacity: 1;
  }
  100% {
    transform: scale(2) translate(var(--tx, 20px), var(--ty, -20px));
    opacity: 0;
  }
}

@keyframes particleFloat {
  0% {
    transform: translateY(0) scale(0);
    opacity: 0;
  }
  20% {
    opacity: 1;
  }
  80% {
    opacity: 0.8;
  }
  100% {
    transform: translateY(-100px) scale(1);
    opacity: 0;
  }
}

@keyframes explode {
  0% {
    transform: translate(0, 0) scale(0);
    opacity: 1;
  }
  100% {
    transform: translate(
      calc(cos(var(--angle)) * 80px),
      calc(sin(var(--angle)) * 80px)
    ) scale(1.5);
    opacity: 0;
  }
}

@keyframes rotateRing {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

@keyframes lightningStrike {
  0%, 100% {
    opacity: 0;
  }
  10%, 30%, 50%, 70% {
    opacity: 1;
  }
  20%, 40%, 60%, 80% {
    opacity: 0.3;
  }
}

@keyframes glowPulse {
  0%, 100% {
    transform: scale(1);
    opacity: 0.3;
  }
  50% {
    transform: scale(1.2);
    opacity: 0.6;
  }
}

@keyframes shimmer {
  0% {
    background-position: 0% center;
  }
  100% {
    background-position: 200% center;
  }
}

@keyframes successPulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
  }
}
</style>
