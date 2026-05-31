import { useState } from 'react'
import { COUNTRIES } from './countries'
import { api } from './api'

type Step = 1|2|3|4|5|6

export default function App() {
  const [step, setStep] = useState<Step>(1)
  const [nfKey, setNfKey] = useState('')
  const [apiHash, setApiHash] = useState('')
  const [apiId, setApiId] = useState('')
  const [country, setCountry] = useState(COUNTRIES[0])
  const [phone, setPhone] = useState('')
  const [code, setCode] = useState('')
  const [password, setPassword] = useState('')
  const [needs2fa, setNeeds2fa] = useState(false)
  const [phoneHash, setPhoneHash] = useState('')
  const [loading, setLoading] = useState(false)
  const [logs, setLogs] = useState<{type:'ok'|'err'|'info', text:string}[]>([])
  const [done, setDone] = useState(false)

  const fullPhone = country.dial + phone.replace(/\D/g,'')

  const log = (t:'ok'|'err'|'info', text:string) => setLogs(l => [...l, {type:t, text}])

  async function sendCode() {
    setLoading(true)
    try {
      const r = await api<{phoneCodeHash:string}>('/send-code', { apiId: Number(apiId), apiHash, phone: fullPhone })
      setPhoneHash(r.phoneCodeHash)
      log('ok', 'SMS kod göndərildi')
      setStep(5)
    } catch (e:any) { log('err', e.message); alert(e.message) }
    setLoading(false)
  }

  async function verifyAndDeploy() {
    setLoading(true)
    setLogs([])
    try {
      log('info', '🔐 Telegram kodu yoxlanılır...')
      const r = await api<{session:string, twoFa?:boolean}>('/verify-code', {
        apiId: Number(apiId), apiHash, phone: fullPhone, phoneCodeHash: phoneHash, code, password
      })
      if (r.twoFa) { setNeeds2fa(true); log('err', '2FA şifrəsi tələb olunur'); setLoading(false); return }
      log('ok', '✓ API təsdiqləndi')
      log('ok', '✓ Session yaradıldı və şifrələndi')
      log('info', '🚀 Northflank servisi yaradılır...')
      const d = await api<{serviceUrl:string}>('/deploy', {
        northflankKey: nfKey, apiId: Number(apiId), apiHash,
        session: r.session, phone: fullPhone
      })
      log('ok', '✓ Northflank servisi yaradıldı')
      log('ok', '✓ Plugin sistemi quruldu')
      log('ok', '✓ Userbot aktiv edildi')
      log('info', `🌐 ${d.serviceUrl}`)
      setDone(true)
    } catch (e:any) { log('err', '❌ ' + e.message) }
    setLoading(false)
  }

  const dots = [1,2,3,4,5].map(i => (
    <div key={i} className={'dot ' + (i < step ? 'done' : i === step ? 'active' : '')} />
  ))

  return (
    <div className="app">
      <div className="brand">
        <div className="logo">R</div>
        <div>
          <h1>Ryhavean Userbot</h1>
          <small>Premium Deploy Panel</small>
        </div>
      </div>

      <div className="glass">
        {!done && <div className="stepper">{dots}</div>}

        {done ? (
          <div className="success">
            <div className="check">✓</div>
            <h2>Ryhavean Userbot uğurla aktiv edildi</h2>
            <p className="lead">Telegram-da <code>.alive</code> yazaraq yoxlayın.</p>
          </div>
        ) : step === 1 ? (
          <>
            <h2>1. Northflank API Key</h2>
            <p className="lead">Userbotunuz Northflank-də avtomatik deploy ediləcək.</p>
            <label>API Key</label>
            <input className="input" type="password" value={nfKey} onChange={e=>setNfKey(e.target.value)} placeholder="nf_..."/>
            <div className="hint">
              <span>API Key yoxdur?</span>
              <a href="https://app.northflank.com/login" target="_blank" rel="noreferrer">API Key Al →</a>
            </div>
            <div style={{height:14}}/>
            <button className="btn" disabled={!nfKey} onClick={()=>setStep(2)}>Davam et</button>
          </>
        ) : step === 2 ? (
          <>
            <h2>2. Telegram API Hash</h2>
            <p className="lead">my.telegram.org saytından əldə edə bilərsiniz.</p>
            <label>API Hash</label>
            <input className="input" value={apiHash} onChange={e=>setApiHash(e.target.value)} placeholder="abcdef0123456789..."/>
            <div className="hint">
              <span>API Hash yoxdur?</span>
              <a href="https://my.telegram.org" target="_blank" rel="noreferrer">API Hash Al →</a>
            </div>
            <div style={{height:14}}/>
            <div className="row">
              <button className="btn ghost" onClick={()=>setStep(1)}>Geri</button>
              <button className="btn" disabled={apiHash.length < 10} onClick={()=>setStep(3)}>Davam et</button>
            </div>
          </>
        ) : step === 3 ? (
          <>
            <h2>3. Telegram API ID</h2>
            <p className="lead">Eyni səhifədən rəqəm formatında.</p>
            <label>API ID</label>
            <input className="input" inputMode="numeric" value={apiId} onChange={e=>setApiId(e.target.value.replace(/\D/g,''))} placeholder="1234567"/>
            <div className="hint">
              <span>API ID yoxdur?</span>
              <a href="https://my.telegram.org" target="_blank" rel="noreferrer">API ID Al →</a>
            </div>
            <div style={{height:14}}/>
            <div className="row">
              <button className="btn ghost" onClick={()=>setStep(2)}>Geri</button>
              <button className="btn" disabled={!apiId} onClick={()=>setStep(4)}>Davam et</button>
            </div>
          </>
        ) : step === 4 ? (
          <>
            <h2>4. Telefon nömrəsi</h2>
            <p className="lead">Telegram doğrulama kodu bu nömrəyə göndəriləcək.</p>
            <label>Ölkə</label>
            <select className="input" value={country.code} onChange={e=>{
              const c = COUNTRIES.find(x=>x.code===e.target.value)!; setCountry(c)
            }}>
              {COUNTRIES.map(c => (
                <option key={c.code} value={c.code}>{c.flag} {c.name} ({c.dial})</option>
              ))}
            </select>
            <div style={{height:12}}/>
            <label>Nömrə</label>
            <div className="row" style={{alignItems:'stretch'}}>
              <div className="input country" style={{maxWidth:110, flex:'0 0 110px'}}>
                <span className="flag">{country.flag}</span>{country.dial}
              </div>
              <input className="input" inputMode="tel" value={phone}
                onChange={e=>setPhone(e.target.value)} placeholder="55 123 45 67" style={{flex:1}}/>
            </div>
            <div style={{height:14}}/>
            <div className="row">
              <button className="btn ghost" onClick={()=>setStep(3)}>Geri</button>
              <button className="btn" disabled={!phone || loading} onClick={sendCode}>
                {loading ? 'Göndərilir...' : 'Kod göndər'}
              </button>
            </div>
          </>
        ) : step === 5 ? (
          <>
            <h2>5. Telegram doğrulama kodu</h2>
            <p className="lead">Telegram-a göndərilən 5 rəqəmli kodu daxil edin.</p>
            <label>Kod</label>
            <input className="input" inputMode="numeric" value={code}
              onChange={e=>setCode(e.target.value.replace(/\D/g,''))} placeholder="• • • • •" maxLength={6}/>
            {needs2fa && (<>
              <div style={{height:12}}/>
              <label>2FA Şifrə</label>
              <input className="input" type="password" value={password}
                onChange={e=>setPassword(e.target.value)} placeholder="Cloud password"/>
            </>)}
            <div style={{height:14}}/>
            <button className="btn" disabled={!code || loading} onClick={verifyAndDeploy}>
              {loading ? 'Qurulur...' : 'Userbotu aktiv et 🚀'}
            </button>
            {logs.length > 0 && (
              <div className="log">
                {logs.map((l,i) => <div key={i} className={l.type}>{l.text}</div>)}
              </div>
            )}
          </>
        ) : null}
      </div>

      <footer>© Ryhavean Userbot · Premium Telegram Suite</footer>
    </div>
  )
}
