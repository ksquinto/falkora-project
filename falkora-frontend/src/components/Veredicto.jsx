import { motion } from 'framer-motion'

/*
  Veredicto — El velocímetro retro mostrando el Hit Score.
  Supernova / Rising Star / Dormant Star.
*/
export default function Veredicto({ verdict }) {
  if (!verdict) return null

  const score = verdict.hit_score || 0
  const label = verdict.falkora_label || ''
  const pred = verdict.prediction || ''
  const probs = verdict.probabilities || {}

  // Color según predicción
  const colors = {
    hit:  { main: '#39ff6a', glow: 'rgba(57,255,106,0.6)' },
    mid:  { main: '#f9c80e', glow: 'rgba(249,200,14,0.6)' },
    flop: { main: '#ff3864', glow: 'rgba(255,56,100,0.6)' },
  }
  const c = colors[pred] || colors.mid

  // Aguja del velocímetro: -90° (score 0) a +90° (score 100)
  const needleAngle = -90 + (score / 100) * 180
  // Arco de progreso
  const arcLength = 377
  const arcOffset = arcLength - (score / 100) * arcLength

  return (
    <div className="flex flex-col items-center py-8">
      <div className="relative" style={{ width: 320, height: 190 }}>
        <svg viewBox="0 0 300 190" width="320" height="190">
          {/* Arco base */}
          <path d="M 30 165 A 120 120 0 0 1 270 165" fill="none"
                stroke="#2d1b4e" strokeWidth="14" strokeLinecap="round" />
          {/* Arco de progreso */}
          <motion.path d="M 30 165 A 120 120 0 0 1 270 165" fill="none"
                stroke="url(#gaugeGrad)" strokeWidth="14" strokeLinecap="round"
                strokeDasharray={arcLength}
                initial={{ strokeDashoffset: arcLength }}
                animate={{ strokeDashoffset: arcOffset }}
                transition={{ duration: 1.5, ease: 'easeOut' }} />
          <defs>
            <linearGradient id="gaugeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#ff3864" />
              <stop offset="50%" stopColor="#f9c80e" />
              <stop offset="100%" stopColor="#39ff6a" />
            </linearGradient>
          </defs>
          {/* Aguja */}
          <motion.line x1="150" y1="165" x2="150" y2="65"
                stroke={c.main} strokeWidth="3" strokeLinecap="round"
                style={{ transformOrigin: '150px 165px', filter: `drop-shadow(0 0 6px ${c.glow})` }}
                initial={{ rotate: -90 }}
                animate={{ rotate: needleAngle }}
                transition={{ duration: 1.5, ease: [0.34, 1.56, 0.64, 1] }} />
          <circle cx="150" cy="165" r="8" fill={c.main} />
          {/* Score */}
          <text x="150" y="135" textAnchor="middle" fill={c.main}
                fontSize="38" fontWeight="bold" fontFamily="Orbitron"
                style={{ filter: `drop-shadow(0 0 10px ${c.glow})` }}>
            {Math.round(score)}
          </text>
          <text x="150" y="155" textAnchor="middle" fill="#9d8bc4"
                fontSize="10" fontFamily="Space Grotesk" letterSpacing="2">
            GRAVITY SCORE
          </text>
        </svg>
      </div>

      {/* Label principal */}
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.8 }}
        className="font-display text-5xl font-bold mt-4 tracking-widest"
        style={{ color: c.main, textShadow: `0 0 30px ${c.glow}` }}>
        {label}
      </motion.div>

      <div className="text-falkora-dim mt-2 tracking-wider text-sm">
        CONFIANZA: {Math.round((verdict.confidence || 0) * 100)}%
      </div>

      {/* Probabilidades */}
      <div className="flex gap-4 mt-8 flex-wrap justify-center">
        {[
          { key: 'flop', label: 'Dormant', icon: '💫', color: '#ff3864' },
          { key: 'mid',  label: 'Rising',  icon: '✨', color: '#f9c80e' },
          { key: 'hit',  label: 'Supernova', icon: '🌟', color: '#39ff6a' },
        ].map(p => (
          <motion.div key={p.key}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1 + Object.keys(probs).indexOf(p.key) * 0.1 }}
            className="panel-card px-6 py-4 min-w-[120px] text-center">
            <div className="text-3xl font-bold font-display" style={{ color: p.color }}>
              {Math.round((probs[p.key] || 0) * 100)}%
            </div>
            <div className="text-xs text-falkora-dim mt-1 tracking-wide">
              {p.icon} {p.label}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
