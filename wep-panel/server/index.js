// Ryhavean Web Panel - Express backend
// Telegram session yaratma + Northflank deploy
import express from 'express'
import cors from 'cors'
import path from 'path'
import { fileURLToPath } from 'url'
import { TelegramClient, Api } from 'telegram'
import { StringSession } from 'telegram/sessions/index.js'
import axios from 'axios'
import crypto from 'crypto'
import 'dotenv/config'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const app = express()
app.use(cors())
app.use(express.json({ limit: '512kb' }))

const sessions = new Map() // phone -> { client, phoneCodeHash }

// DÜZƏLİŞ: açarın uzunluğu nə olursa olsun, SHA-256 ilə HƏMİŞƏ 32 bayta çevrilir.
// Bu, "Invalid key length" xətasını tamamilə aradan qaldırır.
const ENC_KEY = (() => {
  const k = process.env.ENCRYPTION_KEY
  if (!k) {
    console.warn('⚠️  ENCRYPTION_KEY env yoxdur - random yaradılır (yenidən başlatma session-ları sıfırlayacaq)')
    return crypto.randomBytes(32)
  }
  // İstənilən mətn/base64 dəyərini sabit 32 baytlıq açara çevir
  return crypto.createHash('sha256').update(String(k)).digest()
})()

function encrypt(text) {
  const iv = crypto.randomBytes(12)
  const cipher = crypto.createCipheriv('aes-256-gcm', ENC_KEY, iv)
  const enc = Buffer.concat([cipher.update(text, 'utf8'), cipher.final()])
  const tag = cipher.getAuthTag()
  return 'enc:' + Buffer.concat([iv, enc, tag]).toString('base64url')
}

// ===== 1) Send code =====
app.post('/api/send-code', async (req, res) => {
  try {
    const { apiId, apiHash, phone } = req.body
    if (!apiId || !apiHash || !phone) return res.status(400).json({ error: 'apiId, apiHash, phone tələb olunur' })
    const client = new TelegramClient(new StringSession(''), Number(apiId), String(apiHash), { connectionRetries: 3 })
    await client.connect()
    const { phoneCodeHash } = await client.sendCode({ apiId: Number(apiId), apiHash: String(apiHash) }, phone)
    sessions.set(phone, { client, phoneCodeHash })
    res.json({ phoneCodeHash })
  } catch (e) {
    console.error(e)
    res.status(500).json({ error: e.message || 'send-code xətası' })
  }
})

// ===== 2) Verify code =====
app.post('/api/verify-code', async (req, res) => {
  try {
    const { phone, code, password, phoneCodeHash } = req.body
    const entry = sessions.get(phone)
    if (!entry) return res.status(400).json({ error: 'Sesya tapılmadı, kodu yenidən göndərin' })
    const { client } = entry
    const codeHash = phoneCodeHash || entry.phoneCodeHash

    try {
      // DÜZGÜN: GramJS-də invoke yalnız əsl TL Request obyekti qəbul edir
      await client.invoke(
        new Api.auth.SignIn({
          phoneNumber: phone,
          phoneCodeHash: codeHash,
          phoneCode: code,
        })
      )
    } catch (e) {
      if (e.errorMessage === 'SESSION_PASSWORD_NEEDED') {
        if (!password) return res.json({ twoFa: true })
        await client.signInWithPassword(
          { apiId: client.apiId, apiHash: client.apiHash },
          { password: async () => password, onError: (err) => { throw err } }
        )
      } else { throw e }
    }

    const sessionStr = client.session.save()
    const encrypted = encrypt(sessionStr)
    sessions.delete(phone)
    await client.disconnect()
    res.json({ session: encrypted })
  } catch (e) {
    console.error(e)
    res.status(500).json({ error: e.message || 'verify xətası' })
  }
})

// ===== 3) Deploy to Northflank =====
app.post('/api/deploy', async (req, res) => {
  try {
    const { northflankKey, apiId, apiHash, session, phone } = req.body
    if (!northflankKey || !session) return res.status(400).json({ error: 'eksik məlumat' })

    const nf = axios.create({
      baseURL: 'https://api.northflank.com/v1',
      headers: { Authorization: `Bearer ${northflankKey}`, 'Content-Type': 'application/json' },
      timeout: 30000,
    })

    // 1) Userun ilk project-ini tap (yoxdursa yarat)
    let projectId
    try {
      const { data } = await nf.get('/projects')
      projectId = data?.data?.projects?.[0]?.id
    } catch {}
    if (!projectId) {
      const { data } = await nf.post('/projects', {
        name: 'ryhavean-userbot',
        description: 'Ryhavean Userbot auto-deploy',
        region: 'europe-west',
        color: '#7c5cff',
      })
      projectId = data?.data?.id
    }
    if (!projectId) throw new Error('Northflank project yaradıla bilmədi')

    // 2) Userbot servisi yarat (combined service, public image üzərindən)
    const serviceName = 'ryhavean-' + crypto.randomBytes(3).toString('hex')
    const encKey = crypto.randomBytes(32).toString('base64url')

    // QEYD: İstifadəçi öz GitHub repo-sundan da deploy edə bilər.
    // Burada nümunə olaraq DockerHub image istifadə olunur (ENV-lər servisə yazılır).
    await nf.post(`/projects/${projectId}/services/deployment`, {
      name: serviceName,
      description: 'Ryhavean Userbot instance',
      billing: { deploymentPlan: 'nf-compute-20' },
      deployment: {
        instances: 1,
        docker: { configType: 'default' },
        external: {
          imagePath: process.env.USERBOT_IMAGE || 'ryhavean/userbot:latest',
        },
      },
      runtimeEnvironment: {
        API_ID: String(apiId),
        API_HASH: apiHash,
        SESSION_STRING: session,
        ENCRYPTION_KEY: encKey,
        OWNER_PHONE: phone,
      },
    })

    res.json({
      ok: true,
      projectId,
      serviceName,
      serviceUrl: `https://app.northflank.com/s/${projectId}/services/${serviceName}`,
    })
  } catch (e) {
    console.error(e?.response?.data || e)
    res.status(500).json({ error: e?.response?.data?.error?.message || e.message })
  }
})

// ===== Statik fayllar =====
const dist = path.join(__dirname, '..', 'dist')
app.use(express.static(dist))
app.get('*', (_req, res) => res.sendFile(path.join(dist, 'index.html')))

const PORT = process.env.PORT || 8787
app.listen(PORT, () => console.log(`✨ Ryhavean Panel: http://localhost:${PORT}`))
