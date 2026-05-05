import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Lock, User, CheckCircle2, Palette, Globe, CalendarDays, Link2 } from 'lucide-react'
import { authApi, calendarApi, api } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import { useQuery } from '@tanstack/react-query'

// Avatar colour palette (Tailwind-compatible hex values)
const AVATAR_COLORS = [
  '#6366f1', // indigo (default)
  '#8b5cf6', // violet
  '#ec4899', // pink
  '#f43f5e', // rose
  '#ef4444', // red
  '#f97316', // orange
  '#eab308', // yellow
  '#22c55e', // green
  '#14b8a6', // teal
  '#06b6d4', // cyan
  '#3b82f6', // blue
  '#64748b', // slate
]

const TIMEZONES = [
  'Europe/Bratislava',
  'Europe/Prague',
  'Europe/Warsaw',
  'Europe/Vienna',
  'Europe/Berlin',
  'Europe/London',
  'Europe/Paris',
  'America/New_York',
  'America/Chicago',
  'America/Denver',
  'America/Los_Angeles',
  'Asia/Tokyo',
  'Asia/Singapore',
  'Australia/Sydney',
  'UTC',
]

function getInitials(name: string) {
  return name.split(/[\s_]/).map(n => n[0]).slice(0, 2).join('').toUpperCase()
}

export default function SettingsPage() {
  const { user, updateUser } = useAuth()
  const qc = useQueryClient()

  // ── Profile form ─────────────────────────────────────────────────────────
  const [profileForm, setProfileForm] = useState({
    full_name:    user?.full_name ?? '',
    bio:          user?.bio ?? '',
    avatar_color: user?.avatar_color ?? '#6366f1',
    timezone:     user?.timezone ?? 'Europe/Bratislava',
  })
  const [profileOk, setProfileOk] = useState(false)
  const [profileErr, setProfileErr] = useState('')

  const updateProfileMutation = useMutation({
    mutationFn: () => api.patch('/auth/me/profile', profileForm),
    onSuccess: () => {
      updateUser(profileForm)
      setProfileOk(true)
      setProfileErr('')
      setTimeout(() => setProfileOk(false), 3000)
    },
    onError: (e: any) => {
      setProfileErr(e.response?.data?.detail ?? 'Chyba pri ukladaní')
      setProfileOk(false)
    },
  })

  // ── Password form ─────────────────────────────────────────────────────────
  const [pwForm, setPwForm] = useState({ current: '', next: '', confirm: '' })
  const [pwErr, setPwErr] = useState('')
  const [pwOk, setPwOk] = useState(false)

  const changePwMutation = useMutation({
    mutationFn: () => authApi.changePassword(pwForm.current, pwForm.next),
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
    if (!pwForm.current || !pwForm.next) { setPwErr('Vyplň všetky polia'); return }
    if (pwForm.next !== pwForm.confirm)  { setPwErr('Nové heslá sa nezhodujú'); return }
    if (pwForm.next.length < 6)          { setPwErr('Nové heslo musí mať aspoň 6 znakov'); return }
    changePwMutation.mutate()
  }

  // ── iCal token ────────────────────────────────────────────────────────────
  const { data: tokenData } = useQuery<{ token: string | null }>({
    queryKey: ['calendar-token'],
    queryFn:  () => calendarApi.getToken().then(r => r.data),
    staleTime: Infinity,
  })

  const generateTokenMutation = useMutation({
    mutationFn: () => calendarApi.generateToken(),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['calendar-token'] }),
  })

  const icalUrl = tokenData?.token
    ? `${import.meta.env.VITE_API_URL ?? window.location.origin + '/api'}/calendar/${tokenData.token}.ics`
    : null

  const [icalCopied, setIcalCopied] = useState(false)
  async function copyIcal() {
    if (!icalUrl) return
    await navigator.clipboard.writeText(icalUrl)
    setIcalCopied(true)
    setTimeout(() => setIcalCopied(false), 2500)
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Nastavenia</h1>

      {/* ── Profil ─────────────────────────────────────────────────────────── */}
      <div className="card p-6 space-y-5">
        <div className="flex items-center gap-3">
          <User size={18} className="text-brand-500" />
          <h2 className="font-semibold text-gray-900 dark:text-white">Profil</h2>
        </div>

        {/* Avatar preview */}
        <div className="flex items-center gap-4">
          <div
            className="w-16 h-16 rounded-full flex items-center justify-center text-white text-xl font-bold flex-shrink-0 shadow-md transition-colors duration-200"
            style={{ backgroundColor: profileForm.avatar_color }}
          >
            {getInitials(profileForm.full_name || user?.username || 'U')}
          </div>
          <div>
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">@{user?.username}</p>
            <p className="text-xs text-gray-400 capitalize mt-0.5">{user?.role}</p>
          </div>
        </div>

        {/* Colour picker */}
        <div>
          <label className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">
            <Palette size={12} /> Farba avatara
          </label>
          <div className="flex flex-wrap gap-2">
            {AVATAR_COLORS.map(color => (
              <button
                key={color}
                onClick={() => setProfileForm({ ...profileForm, avatar_color: color })}
                style={{ backgroundColor: color }}
                className={`w-7 h-7 rounded-full transition-transform ${
                  profileForm.avatar_color === color ? 'ring-2 ring-offset-2 ring-gray-400 scale-110' : 'hover:scale-105'
                }`}
              />
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1 block">
              Celé meno
            </label>
            <input
              className="input"
              value={profileForm.full_name}
              onChange={e => setProfileForm({ ...profileForm, full_name: e.target.value })}
            />
          </div>
          <div>
            <label className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
              <Globe size={11} /> Časové pásmo
            </label>
            <select
              className="input"
              value={profileForm.timezone}
              onChange={e => setProfileForm({ ...profileForm, timezone: e.target.value })}
            >
              {TIMEZONES.map(tz => (
                <option key={tz} value={tz}>{tz}</option>
              ))}
            </select>
          </div>
          <div className="sm:col-span-2">
            <label className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1 block">
              Bio (voliteľné)
            </label>
            <textarea
              className="input resize-none"
              rows={2}
              placeholder="Krátky popis — rola, odbornosť, tím…"
              value={profileForm.bio}
              onChange={e => setProfileForm({ ...profileForm, bio: e.target.value })}
            />
          </div>
        </div>

        {profileErr && <p className="text-sm text-red-500">{profileErr}</p>}
        {profileOk && (
          <div className="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
            <CheckCircle2 size={16} /> Profil uložený
          </div>
        )}
        <div className="flex justify-end">
          <button
            className="btn-primary text-sm"
            onClick={() => updateProfileMutation.mutate()}
            disabled={updateProfileMutation.isPending || !profileForm.full_name}
          >
            {updateProfileMutation.isPending ? 'Ukladám…' : 'Uložiť profil'}
          </button>
        </div>
      </div>

      {/* ── Zmena hesla ───────────────────────────────────────────────────── */}
      <div className="card p-6 space-y-4">
        <div className="flex items-center gap-3">
          <Lock size={18} className="text-brand-500" />
          <h2 className="font-semibold text-gray-900 dark:text-white">Zmena hesla</h2>
        </div>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1 block">
              Aktuálne heslo
            </label>
            <input
              type="password" className="input" placeholder="••••••••"
              value={pwForm.current}
              onChange={e => setPwForm({ ...pwForm, current: e.target.value })}
            />
          </div>
          <div>
            <label className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1 block">
              Nové heslo
            </label>
            <input
              type="password" className="input" placeholder="Min. 6 znakov"
              value={pwForm.next}
              onChange={e => setPwForm({ ...pwForm, next: e.target.value })}
            />
          </div>
          <div>
            <label className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1 block">
              Potvrď nové heslo
            </label>
            <input
              type="password" className="input" placeholder="••••••••"
              value={pwForm.confirm}
              onChange={e => setPwForm({ ...pwForm, confirm: e.target.value })}
            />
          </div>
        </div>
        {pwErr && <p className="text-sm text-red-500">{pwErr}</p>}
        {pwOk && (
          <div className="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
            <CheckCircle2 size={16} /> Heslo bolo úspešne zmenené
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

      {/* ── iCal integrácia ───────────────────────────────────────────────── */}
      <div className="card p-6 space-y-4">
        <div className="flex items-center gap-3">
          <CalendarDays size={18} className="text-brand-500" />
          <h2 className="font-semibold text-gray-900 dark:text-white">Kalendárová integrácia</h2>
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Pridaj tento odkaz do Google Calendar, Apple Calendar alebo Outlook ako „Predplatenie" kalendára.
          Automaticky sa aktualizuje pri každej zmene.
        </p>
        {icalUrl ? (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <input
                readOnly value={icalUrl}
                className="flex-1 min-w-0 text-xs bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 font-mono text-gray-600 dark:text-gray-400 truncate"
              />
              <button
                onClick={copyIcal}
                className="px-3 py-2 text-xs rounded-lg bg-brand-500 hover:bg-brand-600 text-white transition-colors flex-shrink-0 flex items-center gap-1.5"
              >
                <Link2 size={12} />
                {icalCopied ? 'Skopírované!' : 'Kopírovať'}
              </button>
            </div>
            <div className="flex items-center justify-between">
              <p className="text-xs text-gray-400">
                Len úlohy s <strong>iCal feed</strong> zapnutým sú zahrnuté.
              </p>
              <button
                onClick={() => generateTokenMutation.mutate()}
                className="text-xs text-gray-400 hover:text-red-500 transition-colors"
              >
                Resetovať token
              </button>
            </div>
          </div>
        ) : (
          <button
            onClick={() => generateTokenMutation.mutate()}
            disabled={generateTokenMutation.isPending}
            className="btn-primary text-sm"
          >
            {generateTokenMutation.isPending ? 'Generujem…' : 'Generovať iCal link'}
          </button>
        )}
      </div>
    </div>
  )
}
