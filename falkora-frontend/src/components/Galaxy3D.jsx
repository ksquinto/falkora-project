import { useRef, useEffect, useState } from 'react'
import * as THREE from 'three'

/*
  Galaxy3D — La galaxia Falkora navegable.
  Cada estrella es una canción. Tu track entra como cometa cyan.
  Drag para rotar, scroll para zoom.
*/
export default function Galaxy3D({ stars = [], trackPosition = null, mode = 'extragalactic' }) {
  const mountRef = useRef(null)
  const [hovered, setHovered] = useState(null)
  const stateRef = useRef({})

  useEffect(() => {
    const mount = mountRef.current
    if (!mount) return

    const width = mount.clientWidth
    const height = mount.clientHeight

    // ── Escena ──
    const scene = new THREE.Scene()
    scene.fog = new THREE.FogExp2(0x0a0118, 0.012)

    const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000)
    camera.position.set(0, 0, 40)

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setSize(width, height)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    mount.appendChild(renderer.domElement)

    // ── Estrellas de fondo (decorativas) ──
    const bgGeo = new THREE.BufferGeometry()
    const bgCount = 800
    const bgPos = new Float32Array(bgCount * 3)
    for (let i = 0; i < bgCount * 3; i++) {
      bgPos[i] = (Math.random() - 0.5) * 200
    }
    bgGeo.setAttribute('position', new THREE.BufferAttribute(bgPos, 3))
    const bgMat = new THREE.PointsMaterial({ color: 0x4a3b6e, size: 0.3, transparent: true, opacity: 0.5 })
    const bgStars = new THREE.Points(bgGeo, bgMat)
    scene.add(bgStars)

    // ── Estrellas de canciones ──
    const songGroup = new THREE.Group()
    scene.add(songGroup)

    // Normalizar coordenadas de las estrellas a un rango visible
    let bounds = { minX: Infinity, maxX: -Infinity, minY: Infinity, maxY: -Infinity, minZ: Infinity, maxZ: -Infinity }
    stars.forEach(s => {
      bounds.minX = Math.min(bounds.minX, s.x); bounds.maxX = Math.max(bounds.maxX, s.x)
      bounds.minY = Math.min(bounds.minY, s.y); bounds.maxY = Math.max(bounds.maxY, s.y)
      bounds.minZ = Math.min(bounds.minZ, s.z); bounds.maxZ = Math.max(bounds.maxZ, s.z)
    })
    const scaleRange = (v, min, max) => {
      if (max === min) return 0
      return ((v - min) / (max - min) - 0.5) * 50
    }

    const starMeshes = []
    stars.forEach(s => {
      const color = new THREE.Color(s.color || '#ffffff')
      const geo = new THREE.SphereGeometry(s.size * 0.15, 8, 8)
      const mat = new THREE.MeshBasicMaterial({ color })
      const mesh = new THREE.Mesh(geo, mat)
      mesh.position.set(
        scaleRange(s.x, bounds.minX, bounds.maxX),
        scaleRange(s.y, bounds.minY, bounds.maxY),
        scaleRange(s.z, bounds.minZ, bounds.maxZ)
      )
      mesh.userData = s

      // Glow para supernovas
      if (s.glow) {
        const glowGeo = new THREE.SphereGeometry(s.size * 0.3, 8, 8)
        const glowMat = new THREE.MeshBasicMaterial({
          color, transparent: true, opacity: 0.25
        })
        const glow = new THREE.Mesh(glowGeo, glowMat)
        mesh.add(glow)
      }

      songGroup.add(mesh)
      starMeshes.push(mesh)
    })

    // ── Tu track (cometa cyan) ──
    let trackMesh = null
    if (trackPosition) {
      const geo = new THREE.OctahedronGeometry(1.2, 0)
      const mat = new THREE.MeshBasicMaterial({ color: 0x05d9e8, wireframe: false })
      trackMesh = new THREE.Mesh(geo, mat)
      trackMesh.position.set(
        scaleRange(trackPosition.x, bounds.minX, bounds.maxX),
        scaleRange(trackPosition.y, bounds.minY, bounds.maxY),
        scaleRange(trackPosition.z, bounds.minZ, bounds.maxZ)
      )
      // Halo
      const haloGeo = new THREE.SphereGeometry(2.2, 16, 16)
      const haloMat = new THREE.MeshBasicMaterial({ color: 0x05d9e8, transparent: true, opacity: 0.2 })
      trackMesh.add(new THREE.Mesh(haloGeo, haloMat))
      scene.add(trackMesh)
    }

    // ── Controles de mouse (drag + zoom) ──
    let isDragging = false
    let prevX = 0, prevY = 0
    let rotX = 0, rotY = 0

    const onMouseDown = (e) => { isDragging = true; prevX = e.clientX; prevY = e.clientY }
    const onMouseUp = () => { isDragging = false }
    const onMouseMove = (e) => {
      if (!isDragging) return
      const dx = e.clientX - prevX
      const dy = e.clientY - prevY
      rotY += dx * 0.005
      rotX += dy * 0.005
      prevX = e.clientX
      prevY = e.clientY
    }
    const onWheel = (e) => {
      e.preventDefault()
      camera.position.z += e.deltaY * 0.02
      camera.position.z = Math.max(10, Math.min(80, camera.position.z))
    }

    renderer.domElement.addEventListener('mousedown', onMouseDown)
    window.addEventListener('mouseup', onMouseUp)
    window.addEventListener('mousemove', onMouseMove)
    renderer.domElement.addEventListener('wheel', onWheel, { passive: false })

    // ── Raycaster para hover ──
    const raycaster = new THREE.Raycaster()
    const mouse = new THREE.Vector2()
    const onHoverMove = (e) => {
      const rect = renderer.domElement.getBoundingClientRect()
      mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1
      mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1
      raycaster.setFromCamera(mouse, camera)
      const hits = raycaster.intersectObjects(starMeshes)
      if (hits.length > 0) {
        setHovered(hits[0].object.userData)
      } else {
        setHovered(null)
      }
    }
    renderer.domElement.addEventListener('mousemove', onHoverMove)

    // ── Loop de animación ──
    let frame
    const animate = () => {
      frame = requestAnimationFrame(animate)
      songGroup.rotation.y = rotY
      songGroup.rotation.x = rotX
      bgStars.rotation.y = rotY * 0.3
      if (trackMesh) {
        trackMesh.rotation.x += 0.01
        trackMesh.rotation.y += 0.015
      }
      renderer.render(scene, camera)
    }
    animate()

    stateRef.current = { renderer, scene, camera }

    // ── Resize ──
    const onResize = () => {
      const w = mount.clientWidth, h = mount.clientHeight
      camera.aspect = w / h
      camera.updateProjectionMatrix()
      renderer.setSize(w, h)
    }
    window.addEventListener('resize', onResize)

    // ── Cleanup ──
    return () => {
      cancelAnimationFrame(frame)
      renderer.domElement.removeEventListener('mousedown', onMouseDown)
      window.removeEventListener('mouseup', onMouseUp)
      window.removeEventListener('mousemove', onMouseMove)
      window.removeEventListener('resize', onResize)
      renderer.domElement.removeEventListener('wheel', onWheel)
      renderer.domElement.removeEventListener('mousemove', onHoverMove)
      mount.removeChild(renderer.domElement)
      renderer.dispose()
    }
  }, [stars, trackPosition, mode])

  return (
    <div className="relative w-full h-full">
      <div ref={mountRef} className="w-full h-full rounded-2xl overflow-hidden cursor-grab active:cursor-grabbing" />
      {hovered && (
        <div className="absolute top-4 left-4 panel-card px-4 py-3 pointer-events-none">
          <div className="font-display text-falkora-cyan text-sm">{hovered.name}</div>
          <div className="text-falkora-dim text-xs">{hovered.artist}</div>
          <div className="flex gap-3 mt-1 text-xs">
            <span className="text-falkora-yellow">Pop: {hovered.popularity}</span>
            <span className="text-falkora-dim capitalize">{hovered.genre}</span>
          </div>
        </div>
      )}
      <div className="absolute bottom-4 right-4 text-falkora-dim text-xs pointer-events-none">
        Arrastra para rotar · Scroll para zoom
      </div>
    </div>
  )
}
