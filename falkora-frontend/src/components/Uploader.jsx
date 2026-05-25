import { useState, useEffect, useRef } from 'react'
import { fetchGenres } from '../hooks/useAnalysis'
import { motion, AnimatePresence } from 'framer-motion'

/*
  Uploader — Subida de WAV con extracción automática de features.
  UX simple: arrastra WAV → Falkora analiza → resultado.
*/

export default function Uploader({ onAnalyze, onUploadWav, loading, mode, setMode }) {
  const [genres, setGenres] = useState([])
  const [genre, setGenre] = useState('salsa')
  const [dragActive, setDragActive] = useState(false)
  const [uploadedFile, setUploadedFile] = useState(null)
  const fileInputRef = useRef(null)

  useEffect(() => {
    fetchGenres().then(gs => {
      setGenres(gs)
      const latin = gs.find(g => g.is_latin)
      if (latin) setGenre(latin.name)
    })
  }, [])

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    const files = e.dataTransfer?.files
    if (files && files[0]) {
      handleFile(files[0])
    }
  }

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }

  const handleFile = (file) => {
    // Validar tipo
    const validTypes = ['audio/wav', 'audio/x-wav', 'audio/wave', 'audio/mpeg', 'audio/mp3']
    const validExts = ['.wav', '.mp3', '.WAV', '.MP3']
    const ext = '.' + file.name.split('.').pop()
    
    if (!validTypes.includes(file.type) && !validExts.includes(ext)) {
      alert('Solo archivos WAV o MP3 son aceptados')
      return
    }

    if (file.size > 50 * 1024 * 1024) { // 50MB max
      alert('El archivo es demasiado grande (máx 50MB)')
      return
    }

    setUploadedFile(file)
  }

  const handleAnalyze = () => {
    if (uploadedFile) {
      onUploadWav(uploadedFile, genre, mode)
    }
  }

  return (
    <div className="panel-card p-8 max-w-3xl mx-auto">
      {/* Toggle modo */}
      <div className="flex items-center justify-center gap-2 mb-8">
        <button
          onClick={() => setMode('intragalactic')}
          className={`px-6 py-3 rounded-l-xl font-display text-xs tracking-widest transition-all ${
            mode === 'intragalactic'
              ? 'bg-falkora-purple text-white'
              : 'bg-falkora-bg2 text-falkora-dim'
          }`}>
          🪐 INTRAGALÁCTICO
        </button>
        <button
          onClick={() => setMode('extragalactic')}
          className={`px-6 py-3 rounded-r-xl font-display text-xs tracking-widest transition-all ${
            mode === 'extragalactic'
              ? 'bg-falkora-pink text-white'
              : 'bg-falkora-bg2 text-falkora-dim'
          }`}>
          🌍 EXTRAGALÁCTICO
        </button>
      </div>
      <p className="text-center text-falkora-dim text-xs mb-8">
        {mode === 'intragalactic'
          ? `Comparando solo contra hits de ${genre}`
          : 'Comparando contra todo el universo musical'}
      </p>

      {/* Selección de género */}
      <div className="mb-6">
        <label className="text-falkora-cyan text-xs tracking-wide block mb-2 uppercase">Género del Track</label>
        <select value={genre} onChange={e => setGenre(e.target.value)}
          className="w-full bg-falkora-bg2 border border-falkora-purple/40 rounded-lg px-4 py-3 text-falkora-text font-body">
          {genres.map(g => (
            <option key={g.name} value={g.name}>
              {g.name.charAt(0).toUpperCase() + g.name.slice(1)} ({g.tracks} tracks){g.is_latin ? ' 🌴' : ''}
            </option>
          ))}
        </select>
      </div>

      {/* Drop zone */}
      <div
        className={`relative border-2 border-dashed rounded-xl p-12 text-center transition-all cursor-pointer ${
          dragActive
            ? 'border-falkora-cyan bg-falkora-cyan/10'
            : 'border-falkora-purple/40 bg-falkora-bg2/30 hover:border-falkora-purple hover:bg-falkora-purple/5'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}>
        
        <input
          ref={fileInputRef}
          type="file"
          accept=".wav,.mp3,audio/wav,audio/mpeg"
          onChange={handleFileInput}
          className="hidden"
        />

        <AnimatePresence mode="wait">
          {uploadedFile ? (
            <motion.div
              key="uploaded"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}>
              <div className="text-6xl mb-4">🎵</div>
              <div className="font-display text-falkora-cyan text-lg mb-2">{uploadedFile.name}</div>
              <div className="text-falkora-dim text-sm mb-4">
                {(uploadedFile.size / (1024 * 1024)).toFixed(2)} MB
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); setUploadedFile(null); }}
                className="text-falkora-red text-xs hover:text-falkora-pink transition-colors">
                ✕ Cambiar archivo
              </button>
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}>
              <div className="text-6xl mb-4">📂</div>
              <div className="font-display text-falkora-cyan text-lg mb-2 tracking-wide">
                Arrastra tu WAV aquí
              </div>
              <div className="text-falkora-dim text-sm mb-4">
                o haz click para seleccionar
              </div>
              <div className="text-falkora-dim text-xs">
                Formatos: WAV, MP3 · Máx: 50MB
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Botón analizar */}
      {uploadedFile && (
        <motion.button
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          onClick={handleAnalyze}
          disabled={loading}
          className="w-full mt-6 py-4 rounded-xl font-display text-sm tracking-widest text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          style={{
            background: loading
              ? 'linear-gradient(135deg, #555, #777)'
              : 'linear-gradient(135deg, #05d9e8, #ff2d95)',
            boxShadow: loading ? 'none' : '0 0 30px rgba(255,45,149,0.4)'
          }}>
          {loading ? '✦ EXTRAYENDO FEATURES...' : '✦ ANALIZAR EN FALKORA'}
        </motion.button>
      )}

      {/* Info adicional */}
      <div className="mt-6 p-4 rounded-lg bg-falkora-purple/5 border border-falkora-purple/20">
        <div className="text-falkora-cyan text-xs font-display tracking-wide mb-2">
          ⚡ Ventaja Competitiva de Falkora
        </div>
        <p className="text-falkora-dim text-xs leading-relaxed">
          Analiza tracks <span className="text-falkora-text font-bold">antes de publicarlos</span>.
          Sube demos, mezclas sin masterizar, o cualquier WAV inédito.
          Essentia extrae automáticamente las 15 features que el modelo necesita.
        </p>
      </div>
    </div>
  )
}
