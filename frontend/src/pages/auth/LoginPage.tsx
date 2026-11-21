import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import styles from './LoginPage.module.css'
import { TextField } from '../../components/ui'

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(email, password)
      navigate('/')
    } catch {
      setError('Email ou mot de passe incorrect.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className={styles.page}>
      <svg className={styles.blob} viewBox="0 0 146 150" fill="none" aria-hidden="true">
        <path d="M141.732 53.9621C151.232 83.7621 140.032 119.762 115.732 137.362C91.432 154.862 54.032 153.962 29.632 136.062C5.33202 118.062 -5.96798 83.1621 3.13202 53.8621C12.332 24.5621 42.032 0.862136 72.032 0.862136C101.932 0.762136 132.232 24.1621 141.732 53.9621Z" fill="white" fillOpacity="0.12" />
      </svg>
      <div className={styles.orbit} aria-hidden="true" />
      <section className={styles.card} aria-labelledby="login-title">
        <div className={styles.brand}>DocForge</div>
        <h1 id="login-title" className={styles.title}>Heureux de vous revoir !</h1>
        <p className={styles.subtitle}>Connectez-vous à votre espace.</p>
      <form onSubmit={onSubmit} className={styles.form} aria-busy={loading}>
        {error && <p className={styles.error} role="alert">{error}</p>}
        <TextField
          label="Email"
          id="login-email"
          name="email"
          autoComplete="username"
          placeholder=" "
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <TextField
          label="Mot de passe"
          id="login-password"
          name="password"
          autoComplete="current-password"
          placeholder=" "
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button
          type="submit"
          disabled={loading}
          className={styles.submit}
        >
          {loading ? 'Connexion…' : 'Se connecter'}
        </button>
      </form>
        <p className={styles.footer}>
          Pas encore de compte ? <Link to="/register">Créer une entreprise</Link>
        </p>
      </section>
    </main>
  )
}
