import { useState } from 'react'
import jsPDF from 'jspdf'

export function useExportPDF() {
  const [loading, setLoading] = useState(false)

  const exportAnalysisPDF = async (analysisData, fileName = 'falkora_analysis.pdf') => {
    setLoading(true)

    try {
      if (!analysisData) {
        throw new Error('No hay datos de análisis para exportar')
      }

      // El backend entrega el resultado en esta forma:
      // { verdict, diagnosis, siblings, position }
      // Esta normalización también soporta estructuras planas por compatibilidad.
      const diagnosis = analysisData.diagnosis || analysisData
      const verdict = analysisData.verdict || analysisData
      const audioFeatures = diagnosis.audio_features || analysisData.audio_features || {}
      const brechas = diagnosis.brechas || analysisData.brechas || {}
      const comparacion = diagnosis.comparacion || analysisData.comparacion || ''
      const recomendaciones = diagnosis.recomendaciones || analysisData.recomendaciones || ''
      const genre = diagnosis.genre || analysisData.genre || audioFeatures.genre || 'N/A'
      const mode = analysisData.mode || diagnosis.mode || 'intragalactic'

      const rawGravityScore = diagnosis.gravity_score ?? analysisData.gravity_score
      const gravityScore = Number.isFinite(Number(rawGravityScore))
        ? Number(rawGravityScore)
        : Number(verdict.hit_score ?? 0) / 100

      const doc = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4',
      })

      const width = doc.internal.pageSize.getWidth()
      const height = doc.internal.pageSize.getHeight()
      const margin = 15
      let yPos = margin

      // Colores Falkora
      const colors = {
        cyan: [5, 217, 232],
        pink: [255, 45, 149],
        purple: [168, 85, 247],
        green: [57, 255, 106],
        red: [255, 56, 100],
        yellow: [249, 200, 14],
        dark: [10, 1, 24],
        panel: [26, 15, 46],
        text: [232, 227, 255],
        dim: [157, 139, 196],
      }

      const paintBackground = () => {
        doc.setFillColor(...colors.dark)
        doc.rect(0, 0, width, height, 'F')
      }

      const addPage = () => {
        doc.addPage()
        paintBackground()
        yPos = margin
      }

      const ensureSpace = (needed = 35) => {
        if (yPos > height - needed) addPage()
      }

      const formatNumber = (value) => {
        const n = Number(value)
        if (!Number.isFinite(n)) return 'N/A'
        return Math.abs(n) < 10 ? n.toFixed(3) : n.toFixed(1)
      }

      paintBackground()

      // Header
      doc.setTextColor(...colors.cyan)
      doc.setFontSize(28)
      doc.text('FALKORA', margin, yPos)
      doc.setFontSize(10)
      doc.setTextColor(...colors.dim)
      doc.text('Where Music Becomes Stars', margin, yPos + 8)

      yPos += 22

      // Título
      doc.setTextColor(...colors.pink)
      doc.setFontSize(18)
      doc.text('Análisis Profesional de Track', margin, yPos)
      yPos += 12

      // Info básica
      doc.setTextColor(...colors.text)
      doc.setFontSize(11)
      const infoLines = [
        `Género: ${String(genre).toUpperCase()}`,
        `Fecha de análisis: ${new Date().toLocaleDateString('es-ES')}`,
        `Modo de análisis: ${mode === 'intragalactic' ? 'Intragaláctico (mismo género)' : 'Extragaláctico (todos los géneros)'}`,
      ]

      infoLines.forEach(line => {
        doc.text(line, margin, yPos)
        yPos += 6
      })

      yPos += 8

      // Sección 1: Veredicto
      ensureSpace()
      doc.setTextColor(...colors.cyan)
      doc.setFontSize(14)
      doc.text('1. VEREDICTO', margin, yPos)
      yPos += 8

      doc.setTextColor(...colors.text)
      doc.setFontSize(10)
      const prediction = verdict.prediction ? String(verdict.prediction).toUpperCase() : 'N/A'
      const explanation = verdict.explanation || verdict.falkora_label || 'Sin explicación disponible.'
      const verdictText = `${prediction}: ${explanation}`
      const verdictWrapped = doc.splitTextToSize(verdictText, width - 2 * margin)
      doc.text(verdictWrapped, margin, yPos)
      yPos += verdictWrapped.length * 5 + 8

      // Gravity Score
      ensureSpace(25)
      doc.setTextColor(...colors.green)
      doc.setFontSize(12)
      doc.text(`Gravity Score: ${(gravityScore * 100).toFixed(1)}%`, margin, yPos)
      doc.setTextColor(...colors.dim)
      doc.setFontSize(9)
      doc.text('(Atracción gravitacional hacia el éxito en tu género)', margin, yPos + 6)
      yPos += 16

      // Probabilidades
      if (verdict.probabilities) {
        ensureSpace(25)
        doc.setTextColor(...colors.yellow)
        doc.setFontSize(12)
        doc.text('Probabilidades:', margin, yPos)
        yPos += 7
        doc.setTextColor(...colors.text)
        doc.setFontSize(9)

        const probLabels = {
          flop: 'Dormant',
          mid: 'Rising',
          hit: 'Supernova',
        }

        Object.entries(probLabels).forEach(([key, label]) => {
          const value = Number(verdict.probabilities?.[key] ?? 0)
          doc.text(`• ${label}: ${(value * 100).toFixed(1)}%`, margin + 5, yPos)
          yPos += 5
        })

        yPos += 6
      }

      // Sección 2: ADN Sonoro
      ensureSpace(40)
      doc.setTextColor(...colors.cyan)
      doc.setFontSize(14)
      doc.text('2. ADN SONORO DE LA CANCIÓN', margin, yPos)
      yPos += 8
      doc.setTextColor(...colors.text)
      doc.setFontSize(9)

      const featuresToShow = [
        'danceability', 'energy', 'loudness', 'speechiness',
        'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo'
      ]

      const AUDIO_LABELS = {
        danceability: 'Bailabilidad',
        energy: 'Energía',
        loudness: 'Volumen (dB)',
        speechiness: 'Hablabilidad',
        acousticness: 'Acusticidad',
        instrumentalness: 'Instrumentalidad',
        liveness: 'Vivacidad',
        valence: 'Positividad',
        tempo: 'Tempo (BPM)',
      }

      const presentFeatures = featuresToShow.filter(feature => audioFeatures?.[feature] !== undefined)

      if (presentFeatures.length === 0) {
        doc.setTextColor(...colors.dim)
        doc.text('No se recibieron audio features para este análisis.', margin + 5, yPos)
        yPos += 7
      } else {
        presentFeatures.forEach(feature => {
          ensureSpace(15)
          const label = AUDIO_LABELS[feature] || feature
          const formatted = formatNumber(audioFeatures[feature])
          doc.text(`• ${label}: ${formatted}`, margin + 5, yPos)
          yPos += 5
        })
      }

      yPos += 8

      // Sección 3: Análisis Comparativo
      if (comparacion) {
        ensureSpace(40)
        doc.setTextColor(...colors.cyan)
        doc.setFontSize(14)
        doc.text('3. ANÁLISIS COMPARATIVO', margin, yPos)
        yPos += 8
        doc.setTextColor(...colors.text)
        doc.setFontSize(9)
        const compWrapped = doc.splitTextToSize(String(comparacion), width - 2 * margin)
        doc.text(compWrapped, margin, yPos)
        yPos += compWrapped.length * 5 + 8
      }

      // Sección 4: Brechas Detectadas
      if (brechas && Object.keys(brechas).length > 0) {
        ensureSpace(40)
        doc.setTextColor(...colors.cyan)
        doc.setFontSize(14)
        doc.text('4. BRECHAS DETECTADAS', margin, yPos)
        yPos += 8
        doc.setTextColor(...colors.text)
        doc.setFontSize(9)

        Object.entries(brechas).forEach(([feature, gap]) => {
          ensureSpace(15)
          const label = AUDIO_LABELS[feature] || feature
          const n = Number(gap)
          const sign = n > 0 ? '+' : ''
          const gapPercent = Number.isFinite(n) ? `${sign}${(n * 100).toFixed(1)}%` : 'N/A'
          doc.text(`• ${label}: ${gapPercent}`, margin + 5, yPos)
          yPos += 5
        })

        yPos += 8
      }

      // Sección 5: Recomendaciones
      if (recomendaciones) {
        ensureSpace(40)
        doc.setTextColor(...colors.yellow)
        doc.setFontSize(14)
        doc.text('5. RECOMENDACIONES', margin, yPos)
        yPos += 8
        doc.setTextColor(...colors.text)
        doc.setFontSize(9)
        const recWrapped = doc.splitTextToSize(String(recomendaciones), width - 2 * margin)
        doc.text(recWrapped, margin, yPos)
        yPos += recWrapped.length * 5 + 8
      }

      // Footer
      ensureSpace(20)
      doc.setTextColor(...colors.purple)
      doc.setFontSize(8)
      doc.text(
        'Análisis generado por Falkora — The universe of musical potential',
        width / 2,
        height - 10,
        { align: 'center' }
      )

      doc.save(fileName)
      return true
    } catch (error) {
      console.error('Error exporting PDF:', error)
      return false
    } finally {
      setLoading(false)
    }
  }

  return { exportAnalysisPDF, loading }
}
