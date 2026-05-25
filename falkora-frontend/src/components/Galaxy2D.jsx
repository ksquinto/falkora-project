import { useRef, useEffect, useState, useMemo } from 'react'

/*
  Galaxy2D — Mapa estelar 2D.
  Fix: ResizeObserver para dimensiones reales del canvas,
       estrellas de fondo estáticas (no Math.random() en draw loop),
       separación de transform del loop de animación.
*/
export default function Galaxy2D({ stars = [], trackPosition = null, mode = 'extragalactic' }) {
  const canvasRef      = useRef(null)
  const animFrameRef   = useRef(null)
  const transformRef   = useRef({ x: 0, y: 0, scale: 1 })
  const dragRef        = useRef({ isDragging: false, lastX: 0, lastY: 0 })
  const [transform, setTransform]       = useState({ x: 0, y: 0, scale: 1 })
  const [hovered, setHovered]           = useState(null)
  const [selectedGenre, setSelectedGenre] = useState('all')
  const [canvasSize, setCanvasSize]     = useState({ w: 0, h: 0 })

  // Géneros únicos
  const genres = useMemo(
    () => ['all', ...[...new Set(stars.map(s => s.genre).filter(Boolean))].sort()],
    [stars]
  )

  // Estrellas filtradas
  const filteredStars = useMemo(
    () => selectedGenre === 'all' ? stars : stars.filter(s => s.genre === selectedGenre),
    [stars, selectedGenre]
  )

  // Conteo por tipo
  const counts = useMemo(() => filteredStars.reduce((acc, s) => {
    acc[s.star_type] = (acc[s.star_type] || 0) + 1
    return acc
  }, {}), [filteredStars])

  // Estrellas de fondo ESTÁTICAS (generadas una sola vez)
  const bgStars = useMemo(() => Array.from({ length: 200 }, () => ({
    x: Math.random(),
    y: Math.random(),
    r: Math.random() * 1.2 + 0.3,
  })), [])

  // Ordenar canciones (flops atrás, hits adelante)
  const sortedStars = useMemo(() => [...filteredStars].sort((a, b) => {
    const order = { dormant: 0, rising: 1, supernova: 2 }
    return (order[a.star_type] || 0) - (order[b.star_type] || 0)
  }), [filteredStars])

  // Observar tamaño real del canvas
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ro = new ResizeObserver(entries => {
      for (const e of entries) {
        const { width, height } = e.contentRect
        if (width > 0 && height > 0) setCanvasSize({ w: width, h: height })
      }
    })
    ro.observe(canvas)
    return () => ro.disconnect()
  }, [])

  // Loop de dibujo principal
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || canvasSize.w === 0 || canvasSize.h === 0) return

    const dpr = window.devicePixelRatio || 1
    const W = canvasSize.w
    const H = canvasSize.h
    canvas.width  = W * dpr
    canvas.height = H * dpr
    const ctx = canvas.getContext('2d')
    ctx.scale(dpr, dpr)

    // Pre-calcular normalización
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity
    if (filteredStars.length > 0) {
      filteredStars.forEach(s => {
        if (s.x < minX) minX = s.x; if (s.x > maxX) maxX = s.x
        if (s.y < minY) minY = s.y; if (s.y > maxY) maxY = s.y
      })
    }
    const rangeX = maxX - minX || 1
    const rangeY = maxY - minY || 1
    const padding = 40
    const scaleX = (x) => ((x - minX) / rangeX) * (W - padding * 2) + padding
    const scaleY = (y) => ((y - minY) / rangeY) * (H - padding * 2) + padding

    const draw = () => {
      const t = transformRef.current
      ctx.clearRect(0, 0, W, H)
      ctx.save()
      ctx.translate(t.x, t.y)
      ctx.scale(t.scale, t.scale)

      // Fondo estático
      ctx.fillStyle = 'rgba(74,59,110,0.3)'
      bgStars.forEach(s => {
        ctx.beginPath()
        ctx.arc(s.x * W, s.y * H, s.r, 0, Math.PI * 2)
        ctx.fill()
      })

      // Canciones
      sortedStars.forEach(s => {
        const x = scaleX(s.x)
        const y = scaleY(s.y)
        let size = s.size * 1.5
        if      (s.star_type === 'supernova') size *= 2.5
        else if (s.star_type === 'rising')    size *= 1.8
        else                                   size *= 1.2

        let color = s.color
        let alpha = 1
        if (s.star_type === 'dormant') { color = 'rgba(255,56,100,0.4)'; alpha = 0.5 }

        ctx.globalAlpha = alpha
        ctx.fillStyle   = color
        ctx.beginPath()
        ctx.arc(x, y, size, 0, Math.PI * 2)
        ctx.fill()

        if (s.glow) {
          ctx.save()
          ctx.shadowBlur  = 20
          ctx.shadowColor = s.color
          ctx.fillStyle   = s.color
          ctx.globalAlpha = 0.3
          ctx.beginPath()
          ctx.arc(x, y, size * 2.5, 0, Math.PI * 2)
          ctx.fill()
          ctx.restore()
        }
        ctx.globalAlpha = 1
      })

      // Tu track (cometa cyan animado)
      if (trackPosition) {
        const tx = scaleX(trackPosition.x)
        const ty = scaleY(trackPosition.y)
        const pulse = Math.sin(Date.now() / 400) * 0.4 + 0.6

        ctx.save()
        ctx.shadowBlur  = 25
        ctx.shadowColor = '#05d9e8'
        ctx.fillStyle   = `rgba(5,217,232,${pulse * 0.25})`
        ctx.beginPath()
        ctx.arc(tx, ty, 20, 0, Math.PI * 2)
        ctx.fill()
        ctx.restore()

        ctx.save()
        ctx.translate(tx, ty)
        ctx.rotate(Date.now() / 1200)
        ctx.fillStyle   = '#05d9e8'
        ctx.shadowBlur  = 20
        ctx.shadowColor = '#05d9e8'
        ctx.beginPath()
        ctx.moveTo(0, -10); ctx.lineTo(10, 0)
        ctx.lineTo(0, 10);  ctx.lineTo(-10, 0)
        ctx.closePath()
        ctx.fill()
        ctx.restore()

        ctx.save()
        ctx.shadowBlur = 0
        const label   = 'TU TRACK'
        const labelX  = tx + 18
        const labelY  = ty - 8
        ctx.font      = 'bold 13px Space Grotesk, sans-serif'
        const metrics = ctx.measureText(label)
        ctx.fillStyle = 'rgba(5,217,232,0.2)'
        ctx.fillRect(labelX - 4, labelY - 12, metrics.width + 8, 18)
        ctx.fillStyle = '#05d9e8'
        ctx.fillText(label, labelX, labelY)
        ctx.restore()
      }

      ctx.restore()
    }

    const animate = () => {
      animFrameRef.current = requestAnimationFrame(animate)
      draw()
    }
    animate()

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current)
    }
  }, [filteredStars, sortedStars, bgStars, trackPosition, canvasSize])

  // Sincronizar transformRef con estado (para hover sin re-render del loop)
  useEffect(() => { transformRef.current = transform }, [transform])

  // Eventos del canvas
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || canvasSize.w === 0) return

    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity
    filteredStars.forEach(s => {
      if (s.x < minX) minX = s.x; if (s.x > maxX) maxX = s.x
      if (s.y < minY) minY = s.y; if (s.y > maxY) maxY = s.y
    })
    const rangeX = maxX - minX || 1
    const rangeY = maxY - minY || 1
    const padding = 40
    const W = canvasSize.w, H = canvasSize.h
    const scaleX = (x) => ((x - minX) / rangeX) * (W - padding * 2) + padding
    const scaleY = (y) => ((y - minY) / rangeY) * (H - padding * 2) + padding

    const onMouseDown = (e) => {
      dragRef.current = { isDragging: true, lastX: e.clientX, lastY: e.clientY }
    }
    const onMouseUp = () => { dragRef.current.isDragging = false }
    const onMouseMove = (e) => {
      if (!dragRef.current.isDragging) {
        const rect = canvas.getBoundingClientRect()
        const t    = transformRef.current
        const mx   = (e.clientX - rect.left - t.x) / t.scale
        const my   = (e.clientY - rect.top  - t.y) / t.scale
        let found  = null
        for (const s of filteredStars) {
          const dist = Math.hypot(mx - scaleX(s.x), my - scaleY(s.y))
          if (dist < s.size * 4) { found = s; break }
        }
        setHovered(found)
        return
      }
      const dx = e.clientX - dragRef.current.lastX
      const dy = e.clientY - dragRef.current.lastY
      dragRef.current.lastX = e.clientX
      dragRef.current.lastY = e.clientY
      setTransform(t => ({ ...t, x: t.x + dx, y: t.y + dy }))
    }
    const onWheel = (e) => {
      e.preventDefault()
      const delta = e.deltaY > 0 ? 0.9 : 1.1
      setTransform(t => ({ ...t, scale: Math.max(0.3, Math.min(5, t.scale * delta)) }))
    }

    canvas.addEventListener('mousedown', onMouseDown)
    window.addEventListener('mouseup', onMouseUp)
    window.addEventListener('mousemove', onMouseMove)
    canvas.addEventListener('wheel', onWheel, { passive: false })

    return () => {
      canvas.removeEventListener('mousedown', onMouseDown)
      window.removeEventListener('mouseup', onMouseUp)
      window.removeEventListener('mousemove', onMouseMove)
      canvas.removeEventListener('wheel', onWheel)
    }
  }, [filteredStars, canvasSize])

  return (
    <div className="relative w-full h-full">
      {/* Dropdown de género */}
      <div className="absolute top-4 left-4 z-10">
        <select value={selectedGenre} onChange={e => setSelectedGenre(e.target.value)}
          className="bg-falkora-bg2 border-2 border-falkora-purple text-falkora-cyan px-4 py-2 rounded-lg font-body text-sm tracking-wide cursor-pointer hover:border-falkora-pink transition-all">
          <option value="all">🌍 Universo Completo</option>
          {genres.slice(1).map(g => (
            <option key={g} value={g}>🪐 {g.charAt(0).toUpperCase() + g.slice(1)}</option>
          ))}
        </select>
      </div>

      {/* Canvas */}
      <canvas ref={canvasRef}
        className="w-full h-full rounded-2xl cursor-grab active:cursor-grabbing"
        style={{ background: 'radial-gradient(ellipse at center, rgba(45,27,78,0.3) 0%, #0a0118 70%)' }} />

      {/* Sin estrellas aún */}
      {filteredStars.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-center">
            <div className="text-5xl mb-3 opacity-30">🌌</div>
            <p className="text-falkora-dim text-sm tracking-wide">
              Cargando galaxia… asegúrate de que el backend esté corriendo en :8000
            </p>
          </div>
        </div>
      )}

      {/* Leyenda */}
      <div className="absolute bottom-4 left-4 panel-card px-4 py-3 text-xs space-y-1.5">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-falkora-green" style={{ boxShadow: '0 0 8px #39ff6a' }}></div>
          <span>Supernova ({counts.supernova || 0})</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-falkora-yellow"></div>
          <span>Rising Star ({counts.rising || 0})</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-falkora-red opacity-40"></div>
          <span className="text-falkora-dim">Dormant ({counts.dormant || 0})</span>
        </div>
        <div className="flex items-center gap-2 pt-1 border-t border-falkora-purple/30">
          <div className="w-3 h-3 bg-falkora-cyan" style={{ transform: 'rotate(45deg)' }}></div>
          <span className="text-falkora-cyan">Tu Track</span>
        </div>
      </div>

      {/* Hover info */}
      {hovered && (
        <div className="absolute top-4 right-4 panel-card px-4 py-3 pointer-events-none">
          <div className="font-display text-falkora-cyan text-sm">{hovered.name}</div>
          <div className="text-falkora-dim text-xs">{hovered.artist}</div>
          <div className="flex gap-3 mt-1 text-xs">
            <span className="text-falkora-yellow">Pop: {hovered.popularity}</span>
            <span className="text-falkora-dim capitalize">{hovered.genre}</span>
          </div>
        </div>
      )}

      {/* Info zoom */}
      <div className="absolute bottom-4 right-4 text-falkora-dim text-xs pointer-events-none text-right">
        Arrastra · Scroll · {filteredStars.length.toLocaleString()} estrellas
        <br />
        <span className="text-falkora-purple">Zoom: {Math.round(transform.scale * 100)}%</span>
      </div>
    </div>
  )
}
