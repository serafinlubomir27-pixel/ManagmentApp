import { RefreshCw, Download, Wifi, X } from 'lucide-react'
import { useState } from 'react'
import { usePWA } from '../hooks/usePWA'

export default function PWABanner() {
  const { updateAvailable, offlineReady, isInstallable, install, reload } = usePWA()
  const [dismissedOffline, setDismissedOffline] = useState(false)

  return (
    <>
      {/* New version available */}
      {updateAvailable && (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 bg-brand-600 text-white px-4 py-3 rounded-xl shadow-lg text-sm font-medium">
          <RefreshCw size={16} className="shrink-0" />
          <span>Nová verzia Nodus je dostupná</span>
          <button
            onClick={reload}
            className="ml-1 bg-white/20 hover:bg-white/30 px-3 py-1 rounded-lg transition-colors text-xs font-semibold"
          >
            Aktualizovať
          </button>
        </div>
      )}

      {/* Offline ready toast */}
      {offlineReady && !dismissedOffline && (
        <div className="fixed bottom-4 right-4 z-50 flex items-center gap-3 bg-gray-900 dark:bg-gray-800 text-white px-4 py-3 rounded-xl shadow-lg text-sm max-w-xs">
          <Wifi size={16} className="text-green-400 shrink-0" />
          <span>Nodus beží aj offline</span>
          <button
            onClick={() => setDismissedOffline(true)}
            className="ml-auto text-gray-400 hover:text-white transition-colors"
          >
            <X size={14} />
          </button>
        </div>
      )}

      {/* Install to homescreen */}
      {isInstallable && (
        <div className="fixed bottom-4 right-4 z-50 flex items-center gap-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white px-4 py-3 rounded-xl shadow-lg text-sm max-w-xs">
          <Download size={16} className="text-brand-500 shrink-0" />
          <div>
            <p className="font-semibold">Nainštalovať Nodus</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">Pridať na plochu / homescreen</p>
          </div>
          <button
            onClick={install}
            className="ml-auto bg-brand-500 hover:bg-brand-600 text-white px-3 py-1 rounded-lg text-xs font-semibold transition-colors"
          >
            Inštalovať
          </button>
        </div>
      )}
    </>
  )
}
