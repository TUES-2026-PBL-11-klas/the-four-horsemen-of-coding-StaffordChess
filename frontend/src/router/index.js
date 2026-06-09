import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { 
      path: '/', 
      redirect: '/login' 
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/RegisterView.vue'),
      meta: { guestOnly: true },
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { guestOnly: true },
    },
    {
      path: '/verify-email',
      name: 'verify-email',
      component: () => import('../views/VerifyEmailView.vue'),
      meta: { guestOnly: true },
    },
    {
      path: '/play',
      name: 'play',
      component: () => import('../views/PlayView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/waiting',
      name: 'waiting',
      component: () => import('../views/WaitingView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/game/:id',
      name: 'game',
      component: () => import('../views/GameView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/review/:id',
      name: 'review',
      component: () => import('../views/GameReviewView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('../views/ProfileView.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach((to) => 
{
  const auth = useAuthStore()

  if(to.meta.requiresAuth && !auth.isLoggedIn) 
  {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if(to.meta.guestOnly && auth.isLoggedIn) 
  {
    return { name: 'play' }
  }
})

export default router