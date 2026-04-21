import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { authApi } from '../api/client'
import NodusLogo from '../components/NodusLogo'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await authApi.login(username, password)
      const { access_token, user_id, username: uname, full_name, role } = res.data
      login(access_token, { id: user_id, username: uname, full_name, role })
      navigate('/dashboard')
    } catch (err: any) {
      setError(err.response?.data?.detail ?? 'Prihlásenie zlyhalo')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-bg dark:bg-bg-dark px-4">
      <div className="card w-full max-w-sm p-8">
        {/* Logo */}
        <div className="flex flex-col items-center gap-2 mb-8">
          <NodusLogo variant="wordmark" size={40} />
          <p className="text-xs text-gray-500 dark:text-gray-400 text-center">Projektový manažment na kritickej ceste</p>
        </div>

        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">Prihlásiť sa</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Používateľské meno
            </label>
            <input
              className="input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="admin"
              autoFocus
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Heslo
            </label>
            <input
              type="password"
              className="input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>

          {error && (
            <p className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 px-3 py-2 rounded-lg">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full justify-center flex items-center gap-2 disabled:opacity-60"
          >
            {loading ? 'Prihlasujem…' : 'Prihlásiť sa'}
          </button>
        </form>

        <p className="mt-6 text-xs text-center text-gray-400">
          Demo: <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded">admin</code> / <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded">admin123</code>
        </p>
      </div>
    </div>
  )
}
