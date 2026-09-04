import type { NextRequest } from 'next/server'
import type { Session } from './types'
import { SESSION_COOKIE_NAME } from './constants'
import { decryptJWE } from '@/lib/jwe/decrypt'

const DEFAULT_LOCAL_USER = {
  id: 'delta-local-user',
  username: 'Naxx',
  email: 'naxx@delta.local',
  avatar: 'https://github.com/identicons/naxx.png',
  name: 'Naxx (Local Operator)',
}

export async function getSessionFromCookie(cookieValue?: string): Promise<Session | undefined> {
  if (cookieValue) {
    const decrypted = await decryptJWE<Session>(cookieValue)
    if (decrypted) {
      return {
        created: decrypted.created,
        authProvider: decrypted.authProvider,
        user: decrypted.user,
      }
    }
  }

  // Bypass auth in local standalone mode
  const autoLocal = process.env.ENABLE_LOCAL_AUTH_BYPASS !== 'false'
  if (autoLocal) {
    return {
      created: Date.now(),
      authProvider: 'github',
      user: DEFAULT_LOCAL_USER,
    }
  }
}

export async function getSessionFromReq(req: NextRequest): Promise<Session | undefined> {
  const cookieValue = req.cookies.get(SESSION_COOKIE_NAME)?.value
  return getSessionFromCookie(cookieValue)
}
