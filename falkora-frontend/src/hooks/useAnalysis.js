import { useState, useCallback } from 'react'
import axios from 'axios'

const API = 'http://localhost:8000'

export function useAnalysis() {
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)
  const [result, setResult]   = useState(null)

  const analyze = useCallback(async (features, mode) => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await axios.post(`${API}/analyze`, {
        features,
        mode,
      })
      setResult(data)
      return data
    } catch (e) {
      setError(e.response?.data?.detail || e.message)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  const analyzeUpload = useCallback(async (file, genre, mode) => {
    setLoading(true)
    setError(null)
    try {
      const form = new FormData()
      form.append('file', file)
      const { data } = await axios.post(
        `${API}/analyze/upload?genre=${genre}&mode=${mode}`,
        form,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      )
      setResult(data)
      return data
    } catch (e) {
      const msg = e.response?.data?.detail || e.message
      setError(msg)
      console.error('Upload error:', msg)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  return { analyze, analyzeUpload, loading, error, result }
}

export function useGalaxy() {
  const [stars, setStars] = useState([])
  const [loading, setLoading] = useState(false)

  const loadGalaxy = useCallback(async (mode = 'extragalactic', genre = null) => {
    setLoading(true)
    try {
      const url = genre
        ? `${API}/galaxy?mode=${mode}&genre=${genre}`
        : `${API}/galaxy?mode=${mode}`
      const { data } = await axios.get(url)
      setStars(data.stars || [])
      return data.stars
    } catch (e) {
      console.error('Galaxy load error:', e)
      return []
    } finally {
      setLoading(false)
    }
  }, [])

  return { stars, loadGalaxy, loading }
}

export async function fetchGenres() {
  try {
    const { data } = await axios.get(`${API}/genres`)
    return data.genres || []
  } catch {
    return []
  }
}
