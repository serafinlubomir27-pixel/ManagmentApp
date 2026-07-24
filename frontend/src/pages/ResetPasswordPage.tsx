import { useState, FormEvent } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { authApi } from '../api/client'
import NodusLogo from '../components/NodusLogo'

export default function ResetPasswordPage() {
  const { token = '' } = useParams()
  const navigate = useNavigate()
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [done, setDone] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await authApi.resetPassword(token, password)
      setDone(true)
      setTimeout(() => navigate('/login'), 1500)
    } catch (err: any) {
      setError(err.response?.data?.detail ?? 'Reset zlyhal')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-bg dark:bg-bg-dark px-4">
      <div className="card w-full max-w-sm p-8">
        <div className="flex flex-col items-center gap-2 mb-8">
          <NodusLogo variant="wordmark" size={40} />
        </div>

        {done ? (
          <div className="text-center space-y-4">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Heslo zmenené ✓</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">Presmerúvam na prihlásenie…</p>
          </div>
        ) : (
          <>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">Nové heslo</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <input type="password" className="input" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="min. 8 znakov" minLength={8} autoFocus required />
              {error && (
                <p className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 px-3 py-2 rounded-lg">{error}</p>
              )}
              <button type="submit" disabled={loading} className="btn-primary w-full justify-center flex items-center gap-2 disabled:opacity-60">
                {loading ? 'Ukladám…' : 'Nastaviť heslo'}
              </button>
            </form>
            <p className="mt-6 text-sm text-center text-gray-500 dark:text-gray-400">
              <Link to="/login" className="text-brand-600 dark:text-brand-400 font-medium hover:underline">Späť na prihlásenie</Link>
            </p>
          </>
        )}
      </div>
    </div>
  )
}
