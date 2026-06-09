<template>
  <div class="notfound-page">
    <div class="content">
      <div class="chess-piece">♟</div>
      <h1 class="code">404</h1>
      <p class="msg">This page doesn't exist.</p>
      <router-link to="/" class="btn-home">Go Home</router-link>
    </div>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=DM+Sans:wght@400;500;600&display=swap');
.notfound-page { min-height: 100vh; background: #1a1a1a; display: flex; align-items: center; justify-content: center; font-family: 'DM Sans', sans-serif; color: #e8e0d5; }
.content { text-align: center; display: flex; flex-direction: column; align-items: center; gap: 1rem; }
.chess-piece { font-size: 5rem; animation: sway 2s ease-in-out infinite; }
@keyframes sway { 0%,100% { transform: rotate(-10deg); } 50% { transform: rotate(10deg); } }
.code { font-family: 'Playfair Display', serif; font-size: 5rem; color: #5a9e42; }
.msg { color: #777; font-size: 1.1rem; }
.btn-home { margin-top: 0.5rem; padding: 0.7rem 2rem; background: #5a9e42; color: #fff; border-radius: 8px; text-decoration: none; font-weight: 600; }
.btn-home:hover { background: #7cb662; }
</style>
