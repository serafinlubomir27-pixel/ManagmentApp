/**
 * InvitePage — Public registration page accessed via invite link.
 * URL: /invite/:token
 */
import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { api } from '../api/client'
import NodusLogo from '../components/NodusLogo'
import { CheckCircle2, AlertCircle, Loader2 } from 'lucide-react'

interface InviteInfo {
  valid: boolean
  role: string
  expires_at: string
}

const ROLE_LABEL: Record<string, string> = {
  employee: 'Zamestnanec',
  manager:  'Manažér',
  admin:    'Admin',
}

export default function InvitePage() {
  const { token } = useParams<{ token: string }>()
  const navigate = useNavigate()

  const [inviteInfo, setInviteInfo] = useState<InviteInfo | null>(null)
  const [inviteError, setInviteError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const [form, setForm] = useState({ username: '', full_name: '', password: '', confirm: '' })
  const [formErr, setFormErr] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [success, setSuccess] = useState(false)

  // Load invite info
  useEffect(() => {
    if (!token) return
    api.get(`/invites/${token}/info`)
      .then(r => setInviteInfo(r.data))
      .catch(e => setInviteError(e.response?.data?.detail ?? 'Pozvánka nie je platná'))
      .finally(() => setLoading(false))
  }, [token])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setFormErr('')

    if (!form.username.trim()) { setFormErr('Zadaj používateľské meno'); return }
    if (form.username.length < 3) { setFormErr('Používateľské meno musí mať aspoň 3 znaky'); return }
    if (!form.full_name.trim()) { setFormErr('Zadaj celé meno'); return }
    if (form.password.length < 6) { setFormErr('Heslo musí mať aspoň 6 znakov'); return }
    if (form.password !== form.confirm) { setFormErr('Heslá sa nezhodujú'); return }

    setSubmitting(true)
    try {
      await api.post(`/invites/${token}/accept`, {
        username:   form.username.trim(),
        full_name:  form.full_name.trim(),
        password:   form.password,
      })
      setSuccess(true)
      setTimeout(() => navigate('/login'), 3000)
    } catch (e: any) {
      setFormErr(e.response?.data?.detail ?? 'Chyba pri registrácii')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-bg dark:bg-bg-dark flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <NodusLogo variant="wordmark" size={36} />
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">Projektový manažment s CPM</p>
        </div>

        <div className="card p-8 space-y-6">
          {loading ? (
            <div className="flex items-center justify-center py-8 gap-3 text-gray-400">
              <Loader2 size={20} className="animate-spin" />
              Overujem pozvánku…
            </div>

          ) : inviteError ? (
            <div className="text-center space-y-4">
              <AlertCircle size={40} className="text-red-400 mx-auto" />
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Pozvánka neplatná</h2>
              <p className="text-sm text-gray-500">{inviteError}</p>
              <Link to="/login" className="btn-primary text-sm block text-center">
                Prihlásiť sa
              </Link>
            </div>

          ) : success ? (
            <div className="text-center space-y-4">
              <CheckCircle2 size={40} className="text-green-500 mx-auto" />
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Účet vytvorený!</h2>
              <p className="text-sm text-gray-500">Presmerúvam na prihlásenie…</p>
            </div>

          ) : (
            <>
              <div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">Vytvor účet</h2>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Bol si pozvaný ako{' '}
                  <span className="font-semibold text-brand-600 dark:text-brand-400">
                    {ROLE_LABEL[inviteInfo?.role ?? 'employee']}
                  </span>
                </p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="text-xs text-gray-500 uppercase tracking-wide mb-1 block">
                    Používateľské meno
                  </label>
                  <input
                    className="input"
                    placeholder="napr. jana.novak"
                    value={form.username}
                    onChange={e => setForm({ ...form, username: e.target.value.toLowerCase().replace(/\s/g, '') })}
                    autoComplete="username"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 uppercase tracking-wide mb-1 block">
                    Celé meno
                  </label>
                  <input
                    className="input"
                    placeholder="Jana Nováková"
                    value={form.full_name}
                    onChange={e => setForm({ ...form, full_name: e.target.value })}
                    autoComplete="name"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 uppercase tracking-wide mb-1 block">
                    Heslo
                  </label>
                  <input
                    type="password"
                    className="input"
                    placeholder="Min. 6 znakov"
                    value={form.password}
                    onChange={e => setForm({ ...form, password: e.target.value })}
                    autoComplete="new-password"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500 uppercase tracking-wide mb-1 block">
                    Potvrď heslo
                  </label>
                  <input
                    type="password"
                    className="input"
                    placeholder="••••••••"
                    value={form.confirm}
                    onChange={e => setForm({ ...form, confirm: e.target.value })}
                    autoComplete="new-password"
                  />
                </div>

                {formErr && (
                  <p className="text-sm text-red-500">{formErr}</p>
                )}

                <button
                  type="submit"
                  disabled={submitting}
                  className="btn-primary w-full text-sm"
                >
                  {submitting ? 'Registrujem…' : 'Vytvoriť účet'}
                </button>
              </form>

              <p className="text-center text-xs text-gray-400">
                Máš už účet?{' '}
                <Link to="/login" className="text-brand-500 hover:underline">Prihlásiť sa</Link>
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
