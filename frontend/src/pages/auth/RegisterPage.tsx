import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import styles from './LoginPage.module.css'
import { TextField } from '../../components/ui'

export function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    company_name: '',
    first_name: '',
    last_name: '',
    email: '',
    password: '',
  })
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  function update<K extends keyof typeof form>(key: K, value: string) {
    setForm((f) => ({ ...f, [key]: value }))
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await register(form)
      navigate('/')
    } catch {
      setError("Impossible de créer le compte (email déjà utilisé ?).")
    } finally {
      setLoading(false)
    }
  }

  const fields: Array<{ key: keyof typeof form; label: string; type?: string; autoComplete: string }> = [
    { key: 'company_name', label: 'Nom de l’entreprise', autoComplete: 'organization' },
    { key: 'first_name', label: 'Prénom', autoComplete: 'given-name' },
    { key: 'last_name', label: 'Nom', autoComplete: 'family-name' },
    { key: 'email', label: 'Email', type: 'email', autoComplete: 'email' },
    { key: 'password', label: 'Mot de passe', type: 'password', autoComplete: 'new-password' },
  ]

  return (
    <main className={styles.page}>
      <svg className={styles.blob} viewBox="0 0 146 150" fill="none" aria-hidden="true">
        <path d="M141.732 53.9621C151.232 83.7621 140.032 119.762 115.732 137.362C91.432 154.862 54.032 153.962 29.632 136.062C5.33202 118.062 -5.96798 83.1621 3.13202 53.8621C12.332 24.5621 42.032 0.862136 72.032 0.862136C101.932 0.762136 132.232 24.1621 141.732 53.9621Z" fill="white" fillOpacity="0.12" />
      </svg>
      <div className={styles.orbit} aria-hidden="true" />
      <section className={`${styles.card} ${styles.registerCard}`} aria-labelledby="register-title">
        <div className={styles.brand}>DocForge</div>
        <h1 id="register-title" className={styles.title}>Créer votre entreprise</h1>
        <p className={styles.subtitle}>Votre espace de facturation commence ici.</p>
      <form onSubmit={onSubmit} className={styles.form} aria-busy={loading}>
        {error && <p className={styles.error} role="alert">{error}</p>}
        {fields.map((f) => (
            <TextField
              key={f.key}
              label={f.label}
              id={`register-${f.key}`}
              name={f.key}
              autoComplete={f.autoComplete}
              placeholder=" "
              type={f.type ?? 'text'}
              required
              value={form[f.key]}
              onChange={(e) => update(f.key, e.target.value)}
            />
        ))}
        <button
          type="submit"
          disabled={loading}
          className={styles.submit}
        >
          {loading ? 'Création…' : 'Créer mon compte'}
        </button>
      </form>
        <p className={styles.footer}>
          Déjà un compte ? <Link to="/login">Se connecter</Link>
        </p>
      </section>
    </main>
  )
}
