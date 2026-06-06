import type { CapacitorConfig } from '@capacitor/cli'

const config: CapacitorConfig = {
  appId: 'com.openclaw.portal',
  appName: 'OpenClaw',
  webDir: 'dist',
  server: {
    url: 'https://115.120.202.223',
    cleartext: false,
    androidScheme: 'https',
  },
}

export default config
