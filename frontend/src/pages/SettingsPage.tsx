import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Lock, User, CheckCircle2 } from 'lucide-react'
import { authApi } from '../api/client'
import { useAuth } from '../contexts/AuthContext'

export default function SettingsPage() {
  const { user } = useAuth()

  const [pwForm, setPwForm] = useState({ current: '', next: '', confirm: '' })
  const [pwErr, setPwErr] = useState('')
  const [pwOk, setPwOk] = useState(false)

  const changePwMutation = useMutation({
    mutationFn: () =>
      authApi.changePassword(pwForm.current, pwForm.next),
    onSuccess: () => {
      setPwOk(true)
      setPwErr('')
      setPwForm({ current: '', next: '', confirm: '' })
      setTimeout(() => setPwOk(false), 4000)
    },
    onError: (e: any) => {
      setPwErr(e.response?.data?.detail ?? 'Chyba pri zmene hesla')
      setPwOk(false)
    },
  })

  const handleChangePw = () => {
    setPwErr('')
    if (!pwForm.current || !pwForm.next) {
      setPwErr('Vyplň všetky polia')
      return
    }
    if (pwForm.next !== pwForm.confirm) {
      setPwErr('Nové heslá sa nezhodujú')
      return
    }
    if (pwForm.next.length < 6) {
      setPwErr('Nové heslo musí mať aspoň 6 znakov')
      return
    }
    changePwMutation.mutate()
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Nastavenia</h1>

      {/* Profil */}
      <div className="card p-6 space-y-4">
        <div className="flex items-center gap-3 mb-2">
          <User size={18} className="text-brand-500" />
          <h2 className="font-semibold text-gray-900 dark:text-white">Profil</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1 block">
              Meno
            </label>
            <div className="input bg-gray-50 dark:bg-gray-800/50 cursor-default select-none text-gray-700 dark:text-gray-300">
              {user?.full_name}
            </div>
          </div>
          <div>
            <label className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1 block">
              Používateľské meno
            </label>
            <div className="input bg-gray-50 dark:bg-gray-800/50 cursor-default select-none text-gray-700 dark:text-gray-300">
              @{user?.username}
            </div>
          </div>
          <div>
            <label className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1 block">
              Rola
            </label>
            <div className="input bg-gray-50 dark:bg-gray-800/50 cursor-default select-none text-gray-700 dark:text-gray-300 capitalize">
              {user?.role}
            </div>
          </div>
        </div>
      </div>

      {/* Zmena hesla */}
      <div className="card p-6 space-y-4">
        <div className="flex items-center gap-3 mb-2">
          <Lock size={18} className="text-brand-500" />
          <h2 className="font-semibold text-gray-900 dark:text-white">Zmena hesla</h2>
        </div>

        <div className="space-y-3">
          <div>
            <label className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1 block">
              Aktuálne heslo
            </label>
            <input
              type="password"
              className="input"
              placeholder="••••••••"
              value={pwForm.current}
              onChange={(e) => setPwForm({ ...pwForm, current: e.target.value })}
            />
          </div>
          <div>
            <label className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1 block">
              Nové heslo
            </label>
            <input
              type="password"
              className="input"
              placeholder="Min. 6 znakov"
              value={pwForm.next}
              onChange={(e) => setPwForm({ ...pwForm, next: e.target.value })}
            />
          </div>
          <div>
            <label className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1 block">
              Potvrď nové heslo
            </label>
            <input
              type="password"
              className="input"
              placeholder="••••••••"
              value={pwForm.confirm}
              onChange={(e) => setPwForm({ ...pwForm, confirm: e.target.value })}
            />
          </div>
        </div>

        {pwErr && (
          <p className="text-sm text-red-500">{pwErr}</p>
        )}
        {pwOk && (
          <div className="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
            <CheckCircle2 size={16} />
            Heslo bolo úspešne zmenené
          </div>
        )}

        <div className="flex justify-end">
          <button
            className="btn-primary text-sm"
            onClick={handleChangePw}
            disabled={changePwMutation.isPending}
          >
            {changePwMutation.isPending ? 'Mením heslo…' : 'Zmeniť heslo'}
          </button>
        </div>
      </div>
    </div>
  )
}
