import { useState, useEffect } from 'react'

export function usePWA() {
  const [updateAvailable, setUpdateAvailable] = useState(false)
  const [offlineReady, setOfflineReady] = useState(false)
  const [isInstallable, setIsInstallable] = useState(false)
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null)

  useEffect(() => {
    const onUpdate = () => setUpdateAvailable(true)
    const onOffline = () => setOfflineReady(true)

    window.addEventListener('pwa-update-available', onUpdate)
    window.addEventListener('pwa-offline-ready', onOffline)

    // Install prompt (Android / Chrome desktop)
    const onBeforeInstall = (e: Event) => {
      e.preventDefault()
      setDeferredPrompt(e)
      setIsInstallable(true)
    }
    window.addEventListener('beforeinstallprompt', onBeforeInstall)

    return () => {
      window.removeEventListener('pwa-update-available', onUpdate)
      window.removeEventListener('pwa-offline-ready', onOffline)
      window.removeEventListener('beforeinstallprompt', onBeforeInstall)
    }
  }, [])

  const install = async () => {
    if (!deferredPrompt) return
    deferredPrompt.prompt()
    const { outcome } = await deferredPrompt.userChoice
    if (outcome === 'accepted') {
      setIsInstallable(false)
      setDeferredPrompt(null)
    }
  }

  const reload = () => window.location.reload()

  return { updateAvailable, offlineReady, isInstallable, install, reload }
}
