import { registerSW } from 'virtual:pwa-register'

// Auto-update service worker, show a toast when new version is available
export function registerServiceWorker() {
  const updateSW = registerSW({
    onNeedRefresh() {
      // Show update banner — handled in App.tsx via usePWAUpdate hook
      window.dispatchEvent(new CustomEvent('pwa-update-available'))
    },
    onOfflineReady() {
      console.log('[Nodus PWA] App is ready for offline use')
      window.dispatchEvent(new CustomEvent('pwa-offline-ready'))
    },
    onRegistered(r: ServiceWorkerRegistration | undefined) {
      console.log('[Nodus PWA] Service worker registered:', r)
    },
    onRegisterError(error: unknown) {
      console.warn('[Nodus PWA] Service worker registration failed:', error)
    },
  })

  return updateSW
}
