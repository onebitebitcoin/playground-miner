<template>
  <div class="min-h-[60vh] flex flex-col items-center justify-center text-center px-4 space-y-6">
    <img
      src="/icons/logo-runner.png"
      alt="한입 놀이터 로고"
      class="w-20 h-20"
      decoding="async"
    />
    <div class="space-y-2">
      <h1 class="text-2xl font-bold text-gray-900">페이지를 찾을 수 없습니다</h1>
      <p class="text-gray-600">
        요청하신 페이지가 없거나 이용할 수 없습니다. 메뉴에서 활성화된 기능을 확인해 주세요.
      </p>
    </div>
    <router-link
      class="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-gray-900 text-white text-sm font-semibold shadow-sm hover:bg-gray-800 transition"
      to="/home"
    >
      홈으로 돌아가기
    </router-link>
  </div>
</template>
