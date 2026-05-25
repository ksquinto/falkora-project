import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAnalysis, useGalaxy } from './hooks/useAnalysis'
import Uploader from './components/Uploader'
import Veredicto from './components/Veredicto'
import Galaxy2D from './components/Galaxy2D'
import Diagnosis from './components/Diagnosis'
import Siblings from './components/Siblings'

const TABS = [
  { id: 'uploader',  label: 'Cargador',    icon: '◢' },
  { id: 'veredicto', label: 'Veredicto',   icon: '◢' },
  { id: 'galaxy',    label: 'Galaxia',     icon: '◢' },
  { id: 'diagnosis', label: 'Diagnóstico', icon: '◢' },
  { id: 'siblings',  label: 'Siblings',    icon: '◢' },
]

export default function App() {
  const [tab, setTab] = useState('uploader')
  const [mode, setMode] = useState('intragalactic')
  const { analyze, analyzeUpload, loading, error, result } = useAnalysis()
  const { stars, loadGalaxy } = useGalaxy()
  const [lastFeatures, setLastFeatures] = useState(null)

  // Cargar galaxia y recargar cuando cambia el modo
  useEffect(() => { loadGalaxy(mode) }, [mode])

  // Re-analizar si cambia el modo y ya hay un track analizado
  useEffect(() => {
    if (lastFeatures) {
      analyze(lastFeatures, mode)
    }
  }, [mode])

  const handleAnalyze = async (features) => {
    setLastFeatures(features)
    const data = await analyze(features, mode)
    if (data) setTab('veredicto')
  }

  const handleUploadWav = async (file, genre, modeParam) => {
    const data = await analyzeUpload(file, genre, modeParam)
    if (data) {
      setTab('veredicto')
    }
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="text-center pt-10 pb-6 relative">
        <div className="absolute top-6 left-1/2 -translate-x-1/2 w-48 h-48 rounded-full opacity-10 pointer-events-none"
             style={{ background: 'radial-gradient(circle, #f9c80e 0%, #ff2d95 60%, transparent 70%)' }} />
        <motion.h1
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="font-display text-7xl font-black tracking-[0.2em] gradient-text glow-pink">
          FALKORA
        </motion.h1>
        <p className="text-falkora-cyan tracking-[0.4em] text-xs mt-2 uppercase">
          Where music becomes stars
        </p>
      </header>

      {/* Tabs */}
      <div className="flex gap-2 justify-center mb-8 flex-wrap px-4">
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`px-5 py-2.5 rounded text-xs tracking-widest uppercase transition-all border-2 ${
              tab === t.id
                ? 'border-falkora-pink text-white neon-border-pink'
                : 'border-falkora-bg2 text-falkora-dim hover:border-falkora-cyan hover:text-falkora-cyan'
            }`}>
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {/* Contenido */}
      <main className="max-w-6xl mx-auto px-4 pb-20">
        {/* Error display */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="mb-6 p-4 rounded-lg bg-falkora-red/10 border border-falkora-red/30">
              <div className="text-falkora-red text-sm">
                <span className="font-bold">Error:</span> {error}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <AnimatePresence mode="wait">
          <motion.div key={tab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3 }}>

            {tab === 'uploader' && (
              <Uploader onAnalyze={handleAnalyze}
                        onUploadWav={handleUploadWav}
                        loading={loading}
                        mode={mode}
                        setMode={setMode} />
            )}

            {tab === 'veredicto' && (
              result ? <Veredicto verdict={result.verdict} />
                     : <EmptyState text="Analiza un track primero" />
            )}

            {tab === 'galaxy' && (
              <div className="h-[600px] panel-card overflow-hidden">
                <Galaxy2D stars={stars}
                          trackPosition={result?.position}
                          mode={mode} />
              </div>
            )}

            {tab === 'diagnosis' && (
              result ? <Diagnosis diagnosis={result.diagnosis} />
                     : <EmptyState text="Analiza un track primero" />
            )}

            {tab === 'siblings' && (
              result ? <Siblings siblings={result.siblings} />
                     : <EmptyState text="Analiza un track primero" />
            )}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Footer */}
      <footer className="text-center text-falkora-dim text-xs pb-8 tracking-wide">
        Falkora · The universe of musical potential
      </footer>
    </div>
  )
}

function EmptyState({ text }) {
  return (
    <div className="panel-card p-16 text-center">
      <div className="text-5xl mb-4 opacity-50">🌌</div>
      <p className="text-falkora-dim tracking-wide">{text}</p>
    </div>
  )
}
