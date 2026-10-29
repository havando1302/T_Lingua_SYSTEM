import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

function resolveProxyTarget(configuredValue?: string): string | undefined {
  const configured = configuredValue?.trim()
  if (!configured) return undefined

  const target = new URL(configured)
  if (!['http:', 'https:'].includes(target.protocol)
      || target.username || target.password
      || target.search || target.hash
      || !['', '/'].includes(target.pathname)) {
    throw new Error('VITE_PROXY_TARGET must be an HTTP(S) origin without credentials, path, query, or fragment.')
  }
  return target.origin
}

// Development keeps browser traffic on one origin so CORS-sensitive API calls
// and WebSockets work the same with a Colab backend or a local backend.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const target = resolveProxyTarget(process.env.VITE_PROXY_TARGET || env.VITE_PROXY_TARGET)
  const proxy = target ? {
    '/admin': { target, changeOrigin: true, secure: true },
    '/api': { target, changeOrigin: true, secure: true },
    '/audio': { target, changeOrigin: true, secure: true },
    '/translate': { target, changeOrigin: true, secure: true },
    '/health': { target, changeOrigin: true, secure: true },
    '/ws': { target, changeOrigin: true, secure: true, ws: true },
  } : undefined

  return {
    plugins: [react()],
    server: proxy ? { proxy } : undefined,
  }
})
