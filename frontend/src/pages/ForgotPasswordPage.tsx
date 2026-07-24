import { useState, FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { authApi } from '../api/client'
import NodusLogo from '../components/NodusLogo'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await authApi.forgotPassword(email)
      setSent(true)
    } catch {
      setSent(true) // rovnaká odpoveď bez ohľadu na výsledok (žiadna enumerácia)
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

        {sent ? (
          <div className="text-center space-y-4">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Skontroluj e-mail</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Ak účet s adresou <strong>{email}</strong> existuje, poslali sme naň odkaz na reset hesla. Platí 1 hodinu.
            </p>
            <Link to="/login" className="btn-primary w-full justify-center inline-flex">Späť na prihlásenie</Link>
          </div>
        ) : (
          <>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">Zabudnuté heslo</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">Zadaj e-mail a pošleme ti odkaz na obnovu hesla.</p>
            <form onSubmit={handleSubmit} className="space-y-4">
              <input type="email" className="input" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="jan@acme.sk" autoFocus required />
              <button type="submit" disabled={loading} className="btn-primary w-full justify-center flex items-center gap-2 disabled:opacity-60">
                {loading ? 'Posielam…' : 'Poslať odkaz'}
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
