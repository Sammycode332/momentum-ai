import { Welcome } from './features/Welcome'
import { authClient } from './auth/auth-client'
import { Workspace } from './auth/Workspace'
import { useState } from 'react'
import { PasswordRecovery } from './auth/PasswordRecovery'

function App() {
  const [recovering, setRecovering] = useState(() => new URLSearchParams(location.search).get('flow') === 'reset-password')
  const { data, error, isPending, refetch } = authClient.useSession()
  const email = data?.user?.email

  return (
    <div className="min-h-screen">
      {isPending ? (
        <main><p role="status" className="auth-loading">Restoring your session…</p></main>
      ) : recovering ? (
        <main><PasswordRecovery onBack={() => setRecovering(false)} /></main>
      ) : email ? (
        <Workspace key={data?.user?.id ?? email} email={email}
          name={data?.user?.name === email ? undefined : data?.user?.name?.trim()} onSignedOut={refetch} />
      ) : (
        <main><Welcome onAuthenticated={refetch} sessionError={Boolean(error)} /></main>
      )}
    </div>
  )
}

export default App
