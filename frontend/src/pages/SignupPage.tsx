import { useState, FormEvent } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { authApi } from '../api/client'
import NodusLogo from '../components/NodusLogo'

export default function SignupPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ full_name: '', organization_name: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }))

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await authApi.signup(form)
      const { access_token, user_id, username, full_name, role } = res.data
      login(access_token, { id: user_id, username, full_name, role })
      navigate('/dashboard')
    } catch (err: any) {
      setError(err.response?.data?.detail ?? 'Registrácia zlyhala')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-bg dark:bg-bg-dark px-4 py-8">
      <div className="card w-full max-w-sm p-8">
        <div className="flex flex-col items-center gap-2 mb-8">
          <NodusLogo variant="wordmark" size={40} />
          <p className="text-xs text-gray-500 dark:text-gray-400 text-center">Projektový manažment na kritickej ceste</p>
        </div>

        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">Vytvoriť účet</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tvoje meno</label>
            <input className="input" value={form.full_name} onChange={set('full_name')} placeholder="Ján Novák" autoFocus required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Názov organizácie / tímu</label>
            <input className="input" value={form.organization_name} onChange={set('organization_name')} placeholder="Acme s.r.o." required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">E-mail</label>
            <input type="email" className="input" value={form.email} onChange={set('email')} placeholder="jan@acme.sk" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Heslo</label>
            <input type="password" className="input" value={form.password} onChange={set('password')} placeholder="min. 8 znakov" minLength={8} required />
          </div>

          {error && (
            <p className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 px-3 py-2 rounded-lg">{error}</p>
          )}

          <button type="submit" disabled={loading} className="btn-primary w-full justify-center flex items-center gap-2 disabled:opacity-60">
            {loading ? 'Vytváram…' : 'Vytvoriť účet'}
          </button>
        </form>

        <p className="mt-6 text-sm text-center text-gray-500 dark:text-gray-400">
          Už máš účet?{' '}
          <Link to="/login" className="text-brand-600 dark:text-brand-400 font-medium hover:underline">Prihlásiť sa</Link>
        </p>
      </div>
    </div>
  )
}
