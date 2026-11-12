import { AuthForm } from './auth/AuthForm'
import { authClient } from './auth/auth-client'
import { Workspace } from './auth/Workspace'

function App() {
  const { data, error, isPending, refetch } = authClient.useSession()
  const email = data?.user?.email

  return (
    <main className="grid min-h-screen place-items-center bg-slate-950 p-6 text-slate-50">
      {isPending ? (
        <p role="status" className="text-slate-300">Restoring your session…</p>
      ) : email ? (
        <Workspace email={email} onSignedOut={refetch} />
      ) : (
        <AuthForm onAuthenticated={refetch} sessionError={Boolean(error)} />
      )}
    </main>
  )
}

export default App
