<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-semibold text-slate-800 mb-2">UTXO 시뮬레이션</h1>
      <p class="text-slate-600">비트코인 거래와 UTXO 모델을 체험해보세요</p>
    </div>

    <!-- Transaction Simulator -->
    <div class="bg-white rounded-lg border border-slate-200 p-4 sm:p-6">
      <div class="flex items-center gap-3 mb-4">
        <div class="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center">
          <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
          </svg>
        </div>
        <h2 class="text-lg font-semibold text-slate-800">거래 시뮬레이션</h2>
      </div>

      <div class="grid lg:grid-cols-2 gap-4 lg:gap-6">
        <div class="space-y-4">

          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">받는 주소 개수</label>
            <ModernSelect 
              v-model="recipientCount" 
              @update:modelValue="updateRecipientInputs"
              variant="default"
            >
              <option :value="1">1개 (단일 주소)</option>
              <option :value="2">2개</option>
              <option :value="3">3개</option>
            </ModernSelect>
          </div>

          <!-- Recipient inputs -->
          <div v-for="(recipient, index) in recipients" :key="index" class="space-y-3 p-3 sm:p-4 bg-blue-50 rounded-lg border border-blue-100">
            <h4 class="text-xs sm:text-sm font-medium text-blue-800">받는 사람 {{ index + 1 }}</h4>
            
            <div>
              <label class="block text-[10px] sm:text-xs text-blue-600 mb-1">지갑 선택</label>
              <ModernSelect
                v-model="recipient.walletAddress"
                variant="blue"
                class="text-xs sm:text-sm"
              >
                <option
                  v-for="(wallet, address) in wallets"
                  :key="address"
                  :value="address"
                >
                  {{ formatWalletOption(wallet) }}
                </option>
              </ModernSelect>
            </div>
            
            <div v-if="recipient.walletAddress">
              <label class="block text-[10px] sm:text-xs text-blue-600 mb-1">선택된 주소</label>
              <div class="text-[10px] sm:text-xs text-blue-700 bg-white px-2 py-1 rounded border font-mono break-all">
                <span class="sm:hidden">{{ recipient.walletAddress.slice(0, 15) }}...{{ recipient.walletAddress.slice(-8) }}</span>
                <span class="hidden sm:inline">{{ recipient.walletAddress.slice(0, 20) }}...{{ recipient.walletAddress.slice(-10) }}</span>
              </div>
            </div>
            
            <div>
              <label class="block text-[10px] sm:text-xs text-blue-600 mb-1">보낼 금액 (BTC)</label>
              <input 
                v-model.number="recipient.amount" 
                type="number" 
                step="1" 
                min="1"
                class="w-full px-3 py-2 text-sm border border-blue-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                placeholder="1"
              />
            </div>
          </div>

          <button 
            @click="simulateTransaction" 
            :disabled="!canSendTransaction || !!transactionStatus"
            class="w-full px-4 py-2 sm:py-3 bg-slate-800 hover:bg-slate-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors text-sm sm:text-base"
          >
            <span v-if="transactionStatus" class="flex items-center justify-center gap-2">
              <div class="w-4 h-4 animate-spin border-2 border-current border-t-transparent rounded-full"></div>
              처리 중...
            </span>
            <span v-else>거래 시뮬레이션</span>
          </button>
          
          <div v-if="transactionError" class="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-xs sm:text-sm">
            {{ transactionError }}
          </div>
        </div>

        <div class="space-y-4">
          <!-- Moved full Wallet Status block here -->
          <div class="bg-white rounded-lg border border-slate-200 p-4 sm:p-6">
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-lg font-semibold text-slate-800">내 지갑 상태</h2>
              <button 
                @click="generateInitialUTXOs" 
                class="px-3 sm:px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-lg text-xs sm:text-sm font-medium transition-colors"
              >
                새로 시작
              </button>
            </div>
            
            <div class="grid md:grid-cols-2 gap-4 mb-4">
              <div class="bg-orange-50 rounded-lg p-4 border border-orange-100">
                <div class="text-sm text-orange-600 mb-1">UTXO 개수</div>
                <div class="text-2xl font-bold text-slate-800">{{ myUTXOs.length }}</div>
              </div>
              <div class="bg-blue-50 rounded-lg p-4 border border-blue-100">
                <div class="text-sm text-blue-600 mb-1">총 잔액</div>
                <div class="text-2xl font-bold text-slate-800">{{ totalBalance }} BTC</div>
              </div>
            </div>

            <div class="space-y-2 max-h-48 overflow-y-auto">
              <div v-if="myUTXOs.length === 0" class="text-center py-8 text-slate-500">
                UTXO가 없습니다. '새로 시작' 버튼을 눌러주세요.
              </div>
              <div 
                v-for="utxo in myUTXOs" 
                :key="`my-${utxo.id}`" 
                class="bg-white border rounded-lg p-3 transition-all duration-500"
                :class="{
                  'border-slate-200 hover:shadow-sm': !utxo.isSelected && !utxo.isRemoving && !utxo.isNewlyAdded,
                  // Selected: color-only highlight, no scaling to avoid clipping
                  'border-orange-400 bg-orange-50 shadow-md': utxo.isSelected,
                  'border-red-400 bg-red-50 opacity-50 transform scale-95': utxo.isRemoving,
                  // New UTXO: keep green, remove scaling
                  'border-green-400 bg-green-50 shadow-md': utxo.isNewlyAdded
                }"
              >
                <div class="flex items-center justify-between">
                  <div>
                  <div class="text-sm font-medium" :class="{
                      'text-slate-800': !utxo.isSelected && !utxo.isRemoving && !utxo.isNewlyAdded,
                      'text-orange-800': utxo.isSelected,
                      'text-red-700': utxo.isRemoving,
                      'text-green-800': utxo.isNewlyAdded
                    }">{{ utxo.amount }} BTC</div>
                  </div>
                  <div>
                    <div class="text-xs" :class="{
                      'text-slate-500': !utxo.isSelected && !utxo.isRemoving && !utxo.isNewlyAdded,
                      'text-orange-600': utxo.isSelected,
                      'text-red-600': utxo.isRemoving,
                      'text-green-600': utxo.isNewlyAdded
                    }">{{ utxo.confirmations }} 확인 · {{ getTimeAgo(utxo.createdAt) }}</div>
                    <div v-if="utxo.isSelected" class="text-xs text-orange-600 font-medium mt-1">선택됨</div>
                    <div v-if="utxo.isRemoving" class="text-xs text-red-600 font-medium mt-1">사용됨</div>
                    <div v-if="utxo.isNewlyAdded" class="text-xs text-green-600 font-medium mt-1">새 UTXO</div>
                  </div>
                </div>
              </div>
              
              <!-- New UTXO Animation -->
              <div 
                v-for="newUtxo in newUTXOs" 
                :key="`new-${newUtxo.id}`"
                class="bg-white border border-green-400 rounded-lg p-3 transition-all duration-500 transform"
                :class="{
                  // Remove scaling for new UTXO animation; keep green and pulse
                  'bg-green-50 shadow-md animate-pulse': newUtxo.isNew,
                  'bg-white border-slate-200': !newUtxo.isNew
                }"
              >
                <div class="flex items-center justify-between">
                  <div>
                    <div class="text-sm font-medium" :class="{
                      'text-green-800': newUtxo.isNew,
                      'text-slate-800': !newUtxo.isNew
              }">{{ newUtxo.amount }} BTC</div>
                  </div>
                  <div>
                    <div class="text-xs" :class="{
                      'text-green-600': newUtxo.isNew,
                      'text-slate-500': !newUtxo.isNew
                    }">{{ newUtxo.confirmations }} 확인</div>
                    <div v-if="newUtxo.isNew" class="text-xs text-green-600 font-medium mt-1">
                      {{ newUtxo.isChange ? '잔돈' : '새 UTXO' }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 최근 사용된 UTXO (지속 표시) -->
            <div v-if="recentUsedUTXOs.length" class="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
              <h3 class="text-sm font-semibold text-red-700 mb-2">최근 사용된 UTXO</h3>
              <div class="space-y-2">
                <div 
                  v-for="u in recentUsedUTXOs" 
                  :key="`used-${u.id}`" 
                  class="bg-white border border-red-300 rounded-lg p-3"
                >
                  <div class="flex items-center justify-between">
                    <div class="text-sm font-medium text-red-700">{{ u.amount }} BTC</div>
                    <div class="text-xs text-red-600">{{ getTimeAgo(u.removedAt) }} 사용</div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Transaction Status -->
            <div v-if="transactionStatus" class="mt-4 p-4 rounded-lg" :class="{
              'bg-blue-50 border border-blue-200': transactionStatus === 'selecting',
              'bg-orange-50 border border-orange-200': transactionStatus === 'processing',
              'bg-red-50 border border-red-200': transactionStatus === 'removing',
              'bg-green-50 border border-green-200': transactionStatus === 'creating'
            }">
              <div class="flex items-center gap-2">
                <div v-if="transactionStatus !== 'creating'" class="w-4 h-4 animate-spin border-2 border-current border-t-transparent rounded-full"></div>
                <div v-else class="w-4 h-4 bg-green-500 rounded-full"></div>
                <span class="text-sm font-medium" :class="{
                  'text-blue-700': transactionStatus === 'selecting',
                  'text-orange-700': transactionStatus === 'processing',
                  'text-red-700': transactionStatus === 'removing',
                  'text-green-700': transactionStatus === 'creating'
                }">
                  {{ getTransactionStatusText() }}
                </span>
              </div>
            </div>
          </div>
        
          
        </div>
      </div>
    </div>

    <!-- Current Wallet Status removed (moved into simulator panel above) -->

    <!-- Transaction Visualization -->
    <div v-if="showVisualization" class="bg-white rounded-lg border border-slate-200 p-6 mb-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-slate-800">거래 시각화</h2>
        <button @click="showVisualization = false" class="text-slate-500 hover:text-slate-700">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      
      <div class="relative bg-slate-50 rounded-lg p-8 min-h-96">
        <!-- Transaction Flow Container -->
        <div class="flex items-center justify-between h-full">
          <!-- Input Side -->
          <div class="flex-1 space-y-4">
            <h3 class="text-sm font-semibold text-slate-600 text-center mb-6">입력 (Inputs)</h3>
            <div class="space-y-3">
              <div 
                v-for="(input, index) in visualizationData.inputs" 
                :key="`input-${input.id}`"
                class="bg-white rounded-lg p-4 border-2 transition-all duration-1000"
                :class="[
                  input.isSelected ? 'border-orange-400 bg-orange-50 transform translate-x-2' : 'border-slate-200',
                  input.isConsumed ? 'opacity-50 bg-red-50 border-red-300' : ''
                ]"
                :style="{ animationDelay: `${index * 200}ms` }"
              >
                <div class="flex justify-between items-center">
                  <div>
                    <div class="text-sm font-medium">{{ input.amount }} BTC</div>
                  </div>
                  <div class="w-3 h-3 rounded-full" :class="[
                    input.isSelected ? 'bg-orange-400' : 'bg-slate-300',
                    input.isConsumed ? 'bg-red-400' : ''
                  ]"></div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Center Flow Animation -->
          <div class="flex-shrink-0 px-8 relative">
            <div class="flex flex-col items-center">
              <!-- Transaction Box (ID removed by request) -->
              <div class="bg-blue-500 text-white rounded-lg p-4 mb-4 shadow-lg transform transition-all duration-1000"
                   :class="{ 'scale-110 shadow-xl': visualizationData.isProcessing }">
                <div class="text-center">
                  <div class="text-sm font-semibold">거래</div>
                </div>
              </div>
              
              <!-- Flow Animation -->
              <div v-if="visualizationData.showFlow" class="relative w-32 h-4">
                <div class="absolute top-1/2 left-0 w-full h-0.5 bg-blue-200 transform -translate-y-1/2"></div>
                <div class="absolute top-1/2 left-0 w-4 h-4 bg-blue-500 rounded-full transform -translate-y-1/2 animate-pulse"
                     style="animation: flowRight 2s infinite linear"></div>
              </div>
              
              <!-- Fee Display -->
              <div class="mt-4 text-center">
                <div class="text-xs text-slate-500">수수료</div>
                <div class="text-sm font-medium text-orange-600">{{ visualizationData.fee != null ? visualizationData.fee : 0 }} BTC</div>
              </div>
            </div>
          </div>
          
          <!-- Output Side -->
          <div class="flex-1 space-y-4">
            <h3 class="text-sm font-semibold text-slate-600 text-center mb-6">출력 (Outputs)</h3>
            <div class="space-y-3">
              <div 
                v-for="(output, index) in visualizationData.outputs" 
                :key="`output-${output.id}`"
                class="bg-white rounded-lg p-4 border-2 transition-all duration-1000"
                :class="[
                  output.isNew ? 'border-green-400 bg-green-50 transform -translate-x-2 scale-105' : 'border-slate-200 opacity-30',
                  output.isChange ? 'border-blue-400 bg-blue-50' : ''
                ]"
                :style="{ animationDelay: `${(index + visualizationData.inputs.length) * 200}ms` }"
              >
                <div class="flex justify-between items-center">
                  <div>
                    <div class="text-sm font-medium">{{ output.amount }} BTC</div>
                    <div class="text-xs" :class="output.isChange ? 'text-blue-600' : 'text-slate-500'">
                      {{ output.isChange ? '잔돈 (Change)' : (output.recipientName || 'New Address') }}
                    </div>
                  </div>
                  <div class="w-3 h-3 rounded-full" :class="[
                    output.isNew ? (output.isChange ? 'bg-blue-400' : 'bg-green-400') : 'bg-slate-300'
                  ]"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Progress Steps removed by request -->
      </div>
    </div>

    <!-- Recipient Wallets -->
    <div class="bg-white rounded-lg border border-slate-200 p-6">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-lg bg-orange-100 flex items-center justify-center">
            <svg class="w-4 h-4 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <h2 class="text-lg font-semibold text-slate-800">받는 사람 지갑 현황</h2>
        </div>
        <span class="text-sm text-slate-500">{{ Object.keys(wallets).length }}개 지갑</span>
      </div>

      <div class="grid gap-4">
        <div v-if="Object.keys(wallets).length === 0" class="text-center py-8 text-slate-500">
          아직 받는 사람 지갑이 없습니다. 거래를 시뮬레이션하면 지갑이 생성됩니다.
        </div>
        <div
          v-for="(wallet, address) in wallets"
          :key="address"
          class="border border-slate-200 rounded-lg p-3 sm:p-4 hover:shadow-sm transition-shadow"
        >
          <div class="space-y-3">
            <!-- Mobile-first layout: stacked on small screens -->
            <div class="flex items-start gap-3">
              <div class="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-blue-500 text-white flex items-center justify-center text-xs sm:text-sm font-medium flex-shrink-0">
                {{ wallet.name.charAt(0).toUpperCase() }}
              </div>
              <div class="flex-1 min-w-0">
                <div class="font-medium text-slate-800 text-sm sm:text-base">{{ wallet.name }}</div>
                <!-- Mobile-responsive address display -->
                <div class="text-xs sm:text-sm text-slate-500 font-mono break-all">
                  <span class="sm:hidden">{{ address.slice(0, 12) }}...{{ address.slice(-8) }}</span>
                  <span class="hidden sm:inline">{{ address.slice(0, 20) }}...{{ address.slice(-10) }}</span>
                </div>
              </div>
              <div class="text-right flex-shrink-0">
                <div class="text-base sm:text-lg font-bold text-slate-800">{{ wallet.balance }} BTC</div>
                <div class="text-xs sm:text-sm text-slate-500">{{ wallet.utxos.length }}개 UTXO</div>
              </div>
            </div>

            <!-- Full-width button on mobile -->
            <button
              @click="toggleWalletDetails(address)"
              class="w-full px-3 py-2 text-xs sm:text-sm bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg transition-colors font-medium"
            >
              <span class="sm:hidden">UTXO 보기 ({{ wallet.utxos.length }})</span>
              <span class="hidden sm:inline">UTXO 보기 ({{ wallet.utxos.length }}개)</span>
            </button>
          </div>
          
          <div v-if="expandedWallets.has(address)" class="mt-3 space-y-2 max-h-48 overflow-y-auto">
            <div class="bg-blue-50 rounded-lg p-3 border border-blue-100">
              <h4 class="text-xs sm:text-sm font-semibold text-blue-800 mb-2">보유 UTXO 목록</h4>
              <div v-if="wallet.utxos.length === 0" class="text-center py-4 text-blue-600 text-xs sm:text-sm">
                보유한 UTXO가 없습니다.
              </div>
              <div class="space-y-2">
                <div
                  v-for="utxo in wallet.utxos"
                  :key="utxo.id"
                  class="bg-white rounded-lg p-2 sm:p-3 border border-blue-100"
                >
                  <!-- Mobile-friendly UTXO layout -->
                  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 sm:gap-2">
                    <div class="text-xs sm:text-sm font-medium text-slate-800">{{ utxo.amount }} BTC</div>
                    <div class="text-xs text-slate-500">
                      <div class="break-words">{{ utxo.confirmations }}회 확인 · {{ getTimeAgo(utxo.createdAt) }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Transaction History -->
    <div class="bg-white rounded-lg border border-slate-200 p-6">
      <h2 class="text-lg font-semibold text-slate-800 mb-4">거래 히스토리</h2>
      <div class="space-y-3 max-h-64 overflow-y-auto">
        <div v-if="transactions.length === 0" class="text-center py-8 text-slate-500">
          아직 거래 히스토리가 없습니다.
        </div>
        <div 
          v-for="tx in transactions.slice().reverse()" 
          :key="tx.id"
          class="border border-slate-100 rounded-lg p-4 hover:bg-slate-50 transition-colors"
        >
          <div class="flex items-center justify-between mb-2">
            <span class="font-medium text-slate-800">거래 #{{ tx.id.slice(-8) }}</span>
            <span class="text-sm text-slate-500">{{ new Date(tx.timestamp).toLocaleTimeString() }}</span>
          </div>
          <div class="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div class="text-slate-600 mb-1">입력 ({{ tx.inputs.length }}개)</div>
              <div class="space-y-1">
                <div v-for="input in tx.inputs.slice(0, 2)" :key="input.id" class="text-slate-700">
                  {{ input.amount }} BTC
                </div>
                <div v-if="tx.inputs.length > 2" class="text-slate-500">
                  +{{ tx.inputs.length - 2 }}개 더...
                </div>
              </div>
            </div>
            <div>
              <div class="text-slate-600 mb-1">출력 ({{ tx.outputs.length }}개)</div>
              <div class="space-y-1">
                <div v-for="output in tx.outputs.slice(0, 2)" :key="output.id" class="text-slate-700">
                  {{ output.amount }} BTC 
                  <span v-if="output.isChange" class="text-orange-600">(잔돈)</span>
                </div>
                <div v-if="tx.outputs.length > 2" class="text-slate-500">
                  +{{ tx.outputs.length - 2 }}개 더...
                </div>
              </div>
            </div>
          </div>
          <div class="mt-2 pt-2 border-t border-slate-100 text-xs text-slate-500">
            수수료: {{ tx.fee }} BTC
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, onUnmounted } from 'vue'
import ModernSelect from '../components/ModernSelect.vue'

// Reactive data
const myUTXOs = ref([])
const wallets = reactive({})
const transactions = ref([])
const recentUsedUTXOs = ref([]) // 최근 사용된 UTXO 기록(내 지갑 상태에 표시)
const feeAmount = ref(0.01)
const recipientCount = ref(1)
const recipients = ref([{ walletAddress: '', amount: 1 }])
const transactionError = ref('')
const expandedWallets = ref(new Set())

// Responsive screen width tracking
const screenWidth = ref(window.innerWidth)

// Animation states
const transactionStatus = ref('')
const newUTXOs = ref([])

// Visualization states
const showVisualization = ref(false)
const visualizationData = ref({
  inputs: [],
  outputs: [],
  fee: 0,
  txId: '',
  isProcessing: false,
  showFlow: false
})
const visualizationSteps = ref([
  { label: '선택', completed: false, active: false },
  { label: '처리', completed: false, active: false },
  { label: '소비', completed: false, active: false },
  { label: '생성', completed: false, active: false }
])

// Random name generator
const names = [
  'Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank', 'Grace', 'Henry',
  'Ivy', 'Jack', 'Karen', 'Leo', 'Mia', 'Noah', 'Olivia', 'Paul',
  'Quinn', 'Ruby', 'Sam', 'Tina', 'Uma', 'Victor', 'Wendy', 'Xavier',
  'Yara', 'Zoe', '앨리스', '밥', '찰리', '다이애나',
  '이브', '프랭크', '그레이스', '헨리', '아이비',
  '잭', '카렌', '리오', '미아', '노아', '올리비아'
]

// Generate random segwit address
function generateSegwitAddress() {
  const chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
  let result = 'bc1'
  for (let i = 0; i < 39; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return result
}

// Generate random name
function getRandomName() {
  const usedNames = Object.values(wallets).map(w => w.name)
  const availableNames = names.filter(name => !usedNames.includes(name))
  if (availableNames.length === 0) {
    return `User${Math.floor(Math.random() * 10000)}`
  }
  return availableNames[Math.floor(Math.random() * availableNames.length)]
}

// Generate unique UTXO ID
function generateUTXOId() {
  return 'utxo_' + Math.random().toString(36).substr(2, 16) + Date.now().toString(36)
}

// Generate unique transaction ID
function generateTxId() {
  return 'tx_' + Math.random().toString(36).substr(2, 16) + Date.now().toString(36)
}

// Computed properties
const totalBalance = computed(() => {
  return myUTXOs.value.reduce((sum, utxo) => sum + utxo.amount, 0)
})

const transactionCount = computed(() => {
  return transactions.value.length
})

const canSendTransaction = computed(() => {
  const totalRecipientAmount = recipients.value.reduce((sum, r) => sum + (r.amount || 0), 0)
  const total = totalRecipientAmount
  const hasValidRecipients = recipients.value.every(r => (r.amount || 0) > 0)
  
  const result = total > 0 && total <= totalBalance.value && myUTXOs.value.length > 0 && hasValidRecipients
  
  console.log('canSendTransaction debug:', {
    totalRecipientAmount,
    total,
    totalBalance: totalBalance.value,
    myUTXOsLength: myUTXOs.value.length,
    hasValidRecipients,
    recipients: recipients.value,
    transactionStatus: transactionStatus.value,
    finalResult: result,
    buttonDisabled: !result || !!transactionStatus.value
  })
  
  return result
})

// Sort UTXOs by creation time (newest first)
const sortedMyUTXOs = computed(() => {
  return [...myUTXOs.value].sort((a, b) => (b.createdAt || 0) - (a.createdAt || 0))
})

const sortedNewUTXOs = computed(() => {
  return [...newUTXOs.value].sort((a, b) => (b.createdAt || 0) - (a.createdAt || 0))
})

// Get time ago string
function getTimeAgo(timestamp) {
  if (!timestamp) return '알 수 없음'
  const now = Date.now()
  const diff = now - timestamp
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days > 0) return `${days}일 전`
  if (hours > 0) return `${hours}시간 전`
  if (minutes > 0) return `${minutes}분 전`
  return '방금 전'
}

// Select UTXOs for transaction (simple greedy algorithm)
function selectUTXOs(targetAmount) {
  const sorted = [...myUTXOs.value].sort((a, b) => b.amount - a.amount)
  const selected = []
  let totalSelected = 0
  
  for (const utxo of sorted) {
    selected.push(utxo)
    totalSelected += utxo.amount
    if (totalSelected >= targetAmount) break
  }
  
  return { selected, totalSelected }
}

// Update recipient inputs when count changes
function updateRecipientInputs() {
  const currentCount = recipients.value.length
  const newCount = recipientCount.value
  
  if (newCount > currentCount) {
    // Add new recipients
    for (let i = currentCount; i < newCount; i++) {
      recipients.value.push({ walletAddress: '', amount: 1 })
    }
  } else if (newCount < currentCount) {
    // Remove extra recipients
    recipients.value = recipients.value.slice(0, newCount)
  }
}

// Get wallet balance
function getWalletBalance(wallet) {
  return wallet.utxos.reduce((sum, utxo) => sum + utxo.amount, 0)
}

// Computed: Check if mobile
const isMobile = computed(() => screenWidth.value < 640) // sm breakpoint

// Format wallet option text for mobile compatibility  
function formatWalletOption(wallet) {
  const balance = getWalletBalance(wallet)
  const utxoCount = wallet.utxos.length
  
  if (isMobile.value) {
    // Mobile: compact format with intelligent truncation
    let displayName = wallet.name
    if (wallet.name.length > 8) {
      // Keep more characters for common names
      if (wallet.name.startsWith('satoshi') || wallet.name.startsWith('nakamoto')) {
        displayName = wallet.name.length > 10 ? wallet.name.slice(0, 8) + '...' : wallet.name
      } else {
        displayName = wallet.name.slice(0, 6) + '...'
      }
    }
    return `${displayName} (${utxoCount}, ${balance})`
  } else {
    // Desktop: full format
    return `${wallet.name} (${utxoCount}개 UTXO, ${balance} BTC)`
  }
}

// Create default wallets
function createDefaultWallets() {
  // Create 사토시 wallet
  const satoshiAddress = generateSegwitAddress()
  wallets[satoshiAddress] = {
    name: '사토시',
    address: satoshiAddress,
    utxos: [],
    balance: 0
  }

  // Create 나카모토 wallet
  const nakamotoAddress = generateSegwitAddress()
  wallets[nakamotoAddress] = {
    name: '나카모토',
    address: nakamotoAddress,
    utxos: [],
    balance: 0
  }
}

// Generate initial UTXOs
function generateInitialUTXOs() {
  // Clear existing data
  myUTXOs.value = []
  Object.keys(wallets).forEach(key => delete wallets[key])
  transactions.value = []
  transactionError.value = ''
  // last transaction success banner removed; no reset needed
  recipients.value = [{ walletAddress: '', amount: 1 }]
  recipientCount.value = 1
  transactionStatus.value = ''
  newUTXOs.value = []
  recentUsedUTXOs.value = []
  
  // Create default wallets first
  createDefaultWallets()
  
  // Set default recipient to first wallet (사토시)
  setTimeout(() => {
    const firstWallet = Object.keys(wallets)[0]
    if (firstWallet && recipients.value[0]) {
      recipients.value[0].walletAddress = firstWallet
    }
  }, 100)
  
  // Generate 3-7 random UTXOs with integer amounts
  const count = Math.floor(Math.random() * 5) + 3
  
  for (let i = 0; i < count; i++) {
    const amount = Math.floor(Math.random() * 10) + 1 // 1 to 10 BTC
    myUTXOs.value.push({
      id: generateUTXOId(),
      amount: amount,
      confirmations: Math.floor(Math.random() * 100) + 6,
      createdAt: Date.now()
    })
  }

  // 학습 코스 진행 이벤트: 초기 UTXO 생성 완료 통지
  try {
    window.dispatchEvent(new CustomEvent('lesson:utxo_reset', { detail: { utxoCount: myUTXOs.value.length } }))
  } catch (_) {}
}

// Create or get wallet
function getOrCreateWallet(address) {
  if (!wallets[address]) {
    wallets[address] = {
      name: getRandomName(),
      address: address,
      utxos: [],
      balance: 0
    }
  }
  return wallets[address]
}

// Update wallet balance
function updateWalletBalance(address) {
  const wallet = wallets[address]
  if (wallet) {
    wallet.balance = wallet.utxos.reduce((sum, utxo) => sum + utxo.amount, 0)
  }
}

// Get transaction status text
function getTransactionStatusText() {
  switch (transactionStatus.value) {
    case 'selecting': return 'UTXO를 선택하고 있습니다...'
    case 'processing': return '거래를 처리하고 있습니다...'
    case 'removing': return '사용된 UTXO를 제거하고 있습니다...'
    case 'creating': return '새로운 UTXO를 생성했습니다!'
    default: return ''
  }
}

// Setup visualization
function setupVisualization(selected, outputs, fee, txId) {
  // Add recipient names to outputs for better display
  const outputsWithNames = outputs.map(output => {
    const wallet = wallets[output.address]
    return {
      ...output,
      recipientName: wallet ? wallet.name : 'Unknown',
      isNew: false
    }
  })
  
  visualizationData.value = {
    inputs: selected.map(utxo => ({ ...utxo, isSelected: false, isConsumed: false })),
    outputs: outputsWithNames,
    fee,
    txId,
    isProcessing: false,
    showFlow: false
  }
  
  visualizationSteps.value = [
    { label: '선택', completed: false, active: false },
    { label: '처리', completed: false, active: false },
    { label: '소비', completed: false, active: false },
    { label: '생성', completed: false, active: false }
  ]
  
  showVisualization.value = true
}

// Update visualization step
function updateVisualizationStep(stepIndex, active = false, completed = false) {
  if (stepIndex > 0) {
    visualizationSteps.value[stepIndex - 1].active = false
    visualizationSteps.value[stepIndex - 1].completed = true
  }
  visualizationSteps.value[stepIndex].active = active
  visualizationSteps.value[stepIndex].completed = completed
}

// Simulate transaction with animation
async function simulateTransaction() {
  transactionError.value = ''
  
  // Calculate total amount to send
  const totalSendAmount = recipients.value.reduce((sum, r) => sum + (r.amount || 0), 0)
  const totalNeeded = totalSendAmount
  
  if (totalNeeded <= 0) {
    transactionError.value = '올바른 금액을 입력해주세요.'
    return
  }
  
  if (totalNeeded > totalBalance.value) {
    transactionError.value = '잔액이 부족합니다.'
    return
  }
  
  // Validate recipients
  if (!recipients.value.every(r => (r.amount || 0) > 0)) {
    transactionError.value = '모든 받는 사람의 금액을 입력해주세요.'
    return
  }
  
  // Select UTXOs to spend
  const { selected, totalSelected } = selectUTXOs(totalNeeded)
  
  if (totalSelected < totalNeeded) {
    transactionError.value = '충분한 UTXO를 찾을 수 없습니다.'
    return
  }
  
  // Prepare recipient outputs
  const outputs = []
  
  for (const recipient of recipients.value) {
    let address = recipient.walletAddress
    
    if (!address) {
      transactionError.value = '모든 받는 사람의 지갑을 선택해주세요.'
      return
    }
    
    outputs.push({
      address,
      amount: recipient.amount
    })
  }
  
  // Setup visualization
  const txId = generateTxId()
  setupVisualization(selected, outputs, 0, txId)
  
  // Step 1: Show selected UTXOs
  transactionStatus.value = 'selecting'
  updateVisualizationStep(0, true)
  
  selected.forEach(utxo => {
    const myUtxo = myUTXOs.value.find(u => u.id === utxo.id)
    if (myUtxo) myUtxo.isSelected = true
    
    const vizUtxo = visualizationData.value.inputs.find(u => u.id === utxo.id)
    if (vizUtxo) vizUtxo.isSelected = true
  })
  
  await new Promise(resolve => setTimeout(resolve, 2000))
  
  // Step 2: Process transaction
  transactionStatus.value = 'processing'
  updateVisualizationStep(1, true)
  visualizationData.value.isProcessing = true
  visualizationData.value.showFlow = true
  await new Promise(resolve => setTimeout(resolve, 1500))
  
  // Step 3: Remove used UTXOs with animation
  transactionStatus.value = 'removing'
  updateVisualizationStep(2, true)
  visualizationData.value.isProcessing = false
  
  selected.forEach(utxo => {
    const myUtxo = myUTXOs.value.find(u => u.id === utxo.id)
    if (myUtxo) {
      myUtxo.isSelected = false
      myUtxo.isRemoving = true
    }
    
    const vizUtxo = visualizationData.value.inputs.find(u => u.id === utxo.id)
    if (vizUtxo) {
      vizUtxo.isSelected = false
      vizUtxo.isConsumed = true
    }
  })
  
  await new Promise(resolve => setTimeout(resolve, 1500))
  
  // Actually remove the UTXOs
  const idsToRemove = selected.map(utxo => utxo.id)
  // 기록을 위해 사용된 UTXO를 최근 목록에 추가(최대 5개 유지)
  selected.forEach(utxo => {
    recentUsedUTXOs.value.unshift({
      id: utxo.id,
      amount: utxo.amount,
      confirmations: utxo.confirmations || 0,
      createdAt: utxo.createdAt,
      removedAt: Date.now()
    })
  })
  recentUsedUTXOs.value = recentUsedUTXOs.value.slice(0, 5)
  // 지갑에서 제거
  myUTXOs.value = myUTXOs.value.filter(utxo => !idsToRemove.includes(utxo.id))
  
  // Step 4: Create new UTXOs
  transactionStatus.value = 'creating'
  updateVisualizationStep(3, true)
  newUTXOs.value = []
  
  // Calculate change
  const changeAmount = totalSelected - totalNeeded
  
  // If there will be a change output, include it in the visualization outputs list
  // so users can see the change UTXO being created (highlighted when ready).
  if (changeAmount > 0) {
    visualizationData.value.outputs.push({
      id: `change-${txId}`,
      address: 'change',
      amount: changeAmount,
      isNew: false,
      isChange: true,
      recipientName: 'Change'
    })
  }
  
  // Create transaction record
  const transaction = {
    id: txId,
    timestamp: Date.now(),
    inputs: selected.map(utxo => ({ ...utxo })),
    outputs: [],
    fee: 0
  }
  
  // Add recipient outputs
  outputs.forEach(output => {
    const wallet = getOrCreateWallet(output.address)
    const newUTXO = {
      id: generateUTXOId(),
      amount: output.amount,
      confirmations: 0
    }
    
    wallet.utxos.push(newUTXO)
    updateWalletBalance(output.address)
    
    transaction.outputs.push({
      ...newUTXO,
      address: output.address,
      isChange: false
    })
  })
  
  // Add change output if needed with animation  
  if (changeAmount > 0) {
    const changeUTXO = {
      id: generateUTXOId(),
      amount: Math.round(changeAmount),
      confirmations: 0,
      isNew: true,
      isChange: true
    }
    
    newUTXOs.value.push(changeUTXO)
    
    transaction.outputs.push({
      ...changeUTXO,
      address: 'change',
      isChange: true
    })
    
    // Update visualization
    const vizOutput = visualizationData.value.outputs.find(o => o.isChange)
    if (vizOutput) vizOutput.isNew = true
  }
  
  // Update visualization outputs
  outputs.forEach(output => {
    const vizOutput = visualizationData.value.outputs.find(o => o.address === output.address)
    if (vizOutput) vizOutput.isNew = true
  })
  
  await new Promise(resolve => setTimeout(resolve, 2000))
  
  // Move new UTXOs to main list and clear animation
  const utxosToAdd = []
  newUTXOs.value.forEach(utxo => {
    if (utxo.isChange) {
      const finalUtxo = {
        id: utxo.id,
        amount: utxo.amount,
        confirmations: utxo.confirmations
      }
      utxosToAdd.push(finalUtxo)
    }
  })
  
  // Clear new UTXOs first, then add to main list
  newUTXOs.value = []
  await new Promise(resolve => setTimeout(resolve, 100))
  
  utxosToAdd.forEach(utxo => {
    // Mark as newly added for green highlight within wallet list (지속 표시)
    const withFlag = { ...utxo, isNewlyAdded: true, createdAt: Date.now() }
    myUTXOs.value.push(withFlag)
  })
  
  // Add transaction to history
  transactions.value.push(transaction)
  
  // Clear animation states from all UTXOs
  myUTXOs.value.forEach(utxo => {
    delete utxo.isSelected
    delete utxo.isRemoving
  })
  
  // Complete visualization
  updateVisualizationStep(3, false, true)
  
  // 학습 코스 진행 이벤트: 거래 생성 완료 통지
  try {
    const outSummary = transaction.outputs.map(o => ({ amount: o.amount, isChange: !!o.isChange }))
    window.dispatchEvent(new CustomEvent('lesson:utxo_tx', { detail: { id: txId, outputs: outSummary, inputs: selected.map(s => s.amount) } }))
  } catch (_) {}

  // Reset form and status
  // No fee needed; keep recipient default to the first wallet
  recipients.value = [{ walletAddress: '', amount: 1 }]
  recipientCount.value = 1
  const firstWalletAfterTx = Object.keys(wallets)[0]
  if (firstWalletAfterTx && recipients.value[0]) {
    recipients.value[0].walletAddress = firstWalletAfterTx
  }
  
  // Clear status after a short delay
  setTimeout(() => {
    transactionStatus.value = ''
  }, 1000)
  
  // Success banner removed
}

// Toggle wallet details
function toggleWalletDetails(address) {
  if (expandedWallets.value.has(address)) {
    expandedWallets.value.delete(address)
  } else {
    expandedWallets.value.add(address)
  }
}

// Responsive screen width management
function handleResize() {
  screenWidth.value = window.innerWidth
}

// Lifecycle hooks
onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

// Initialize with some UTXOs
generateInitialUTXOs()
</script>

<style scoped>
@keyframes flowRight {
  0% {
    transform: translateX(0) translateY(-50%);
  }
  100% {
    transform: translateX(120px) translateY(-50%);
  }
}
</style>
