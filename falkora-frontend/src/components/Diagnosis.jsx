import { useRef, useEffect } from 'react'

/*
  Diagnosis — Radar chart (tu ADN vs hits) + brechas + explicación IA.
*/
export default function Diagnosis({ diagnosis }) {
  const canvasRef = useRef(null)

  useEffect(() => {
    if (!diagnosis || !canvasRef.current) return
    drawRadar(canvasRef.current, diagnosis.radar)
  }, [diagnosis])

  if (!diagnosis) return null

  const { gaps = [], explanation = '', gravity_score = 0, reference_n = 0, mode } = diagnosis

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Radar */}
      <div className="panel-card p-6">
        <h3 className="font-display text-falkora-cyan text-sm tracking-widest mb-4 uppercase">
          ◢ ADN Sonoro vs {mode === 'intragalactic' ? `Hits de ${diagnosis.genre}` : 'Hits Globales'}
        </h3>
        <canvas ref={canvasRef} width={400} height={340} className="w-full" />
        <div className="flex gap-6 justify-center mt-2 text-xs">
          <span className="flex items-center gap-2 text-falkora-cyan">
            <span className="w-3 h-3 rounded-sm bg-falkora-cyan inline-block" /> Tu track
          </span>
          <span className="flex items-center gap-2 text-falkora-pink">
            <span className="w-3 h-3 rounded-sm bg-falkora-pink inline-block" /> Hits
          </span>
        </div>
      </div>

      {/* Brechas */}
      <div className="panel-card p-6">
        <h3 className="font-display text-falkora-cyan text-sm tracking-widest mb-4 uppercase">
          ◢ Brechas Detectadas
        </h3>
        <div className="space-y-4">
          {gaps.map(g => {
            const ok = g.status === 'ok'
            const color = ok ? '#39ff6a' : (g.status === 'below' ? '#ff3864' : '#f9c80e')
            const sign = g.delta > 0 ? '+' : ''
            return (
              <div key={g.feature}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="capitalize text-falkora-text">{g.feature}</span>
                  <span style={{ color }} className="font-bold">
                    {sign}{g.delta.toFixed(2)} {ok ? '✓' : '⚠'}
                  </span>
                </div>
                <div className="relative h-2 bg-falkora-bg2 rounded-full">
                  <div className="absolute top-0 h-full rounded-full bg-falkora-cyan"
                       style={{ width: `${Math.min(g.yours * 100, 100)}%` }} />
                  <div className="absolute -top-1 w-1 h-4 bg-falkora-pink"
                       style={{ left: `${Math.min(g.target * 100, 100)}%`, boxShadow: '0 0 8px #ff2d95' }} />
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Explicación IA */}
      <div className="lg:col-span-2 relative panel-card p-6 mt-2"
           style={{ background: 'linear-gradient(135deg, rgba(168,85,247,0.12), rgba(255,45,149,0.06))' }}>
        <div className="absolute -top-3 left-6 bg-falkora-purple text-white text-xs px-3 py-1 rounded-full tracking-widest uppercase">
          ⚡ Análisis IA
        </div>
        <div className="flex items-center gap-4 mb-4 mt-2">
          <div>
            <div className="font-display text-4xl font-bold gradient-text">{gravity_score}</div>
            <div className="text-xs text-falkora-dim tracking-wide">GRAVITY SCORE</div>
          </div>
          <div className="text-xs text-falkora-dim border-l border-falkora-purple/30 pl-4">
            Comparado contra<br />
            <span className="text-falkora-cyan font-bold">{reference_n}</span> hits de referencia
          </div>
        </div>
        <p className="text-falkora-text leading-relaxed text-sm">{explanation}</p>
      </div>
    </div>
  )
}

function drawRadar(canvas, radar) {
  if (!radar) return
  const dpr = window.devicePixelRatio || 1
  const W = 400, H = 340
  canvas.width = W * dpr
  canvas.height = H * dpr
  const ctx = canvas.getContext('2d')
  ctx.scale(dpr, dpr)
  ctx.clearRect(0, 0, W, H)

  const cx = W / 2, cy = H / 2, R = 110
  const axes = radar.axes || []
  const yours = radar.yours || []
  const target = radar.target || []
  const n = axes.length
  if (n === 0) return

  // Grid
  for (let ring = 1; ring <= 4; ring++) {
    ctx.beginPath()
    for (let i = 0; i <= n; i++) {
      const a = (Math.PI * 2 * i / n) - Math.PI / 2
      const x = cx + Math.cos(a) * R * ring / 4
      const y = cy + Math.sin(a) * R * ring / 4
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
    }
    ctx.strokeStyle = '#2d1b4e'
    ctx.lineWidth = 1
    ctx.stroke()
  }

  // Axes + labels
  axes.forEach((ax, i) => {
    const a = (Math.PI * 2 * i / n) - Math.PI / 2
    const x = cx + Math.cos(a) * R
    const y = cy + Math.sin(a) * R
    ctx.beginPath()
    ctx.moveTo(cx, cy)
    ctx.lineTo(x, y)
    ctx.strokeStyle = '#2d1b4e'
    ctx.stroke()
    ctx.fillStyle = '#9d8bc4'
    ctx.font = '10px Space Grotesk'
    ctx.textAlign = 'center'
    ctx.fillText(ax, cx + Math.cos(a) * (R + 20), cy + Math.sin(a) * (R + 20) + 3)
  })

  const poly = (data, stroke, fill) => {
    ctx.beginPath()
    data.forEach((v, i) => {
      const a = (Math.PI * 2 * i / n) - Math.PI / 2
      const x = cx + Math.cos(a) * R * Math.min(v, 1)
      const y = cy + Math.sin(a) * R * Math.min(v, 1)
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
    })
    ctx.closePath()
    ctx.fillStyle = fill
    ctx.fill()
    ctx.strokeStyle = stroke
    ctx.lineWidth = 2
    ctx.stroke()
  }

  poly(target, '#ff2d95', 'rgba(255,45,149,0.12)')
  poly(yours, '#05d9e8', 'rgba(5,217,232,0.18)')
}
