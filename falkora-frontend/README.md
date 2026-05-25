# 🌌 Falkora Frontend

> *"Where music becomes stars."*

Frontend React con galaxia 3D navegable, toggle intra/extragaláctico en vivo, y toda la experiencia visual synthwave de Falkora.

---

## Stack

- **React 18** — componentes y state
- **Three.js** — galaxia 3D navegable con WebGL
- **Vite** — bundler ultrarrápido
- **TailwindCSS** — estilización synthwave
- **Framer Motion** — animaciones fluidas
- **Axios** — llamadas al backend

---

## Instalación

### 1. Instalar Node.js (si no lo tienes)
Descarga desde: https://nodejs.org/ (versión LTS recomendada)

### 2. Instalar dependencias
```bash
cd falkora-frontend
npm install
```

Esto descarga todas las librerías (React, Three.js, etc). Tarda ~2 minutos.

### 3. Verificar que el backend esté corriendo
El frontend necesita que el backend esté vivo en `http://localhost:8000`.

En otra terminal (PowerShell):
```powershell
cd "C:\Users\ksqr9\OneDrive\Falkora project\falkora-backend"
.\venv\Scripts\Activate
python -m uvicorn main:app --reload --port 8000
```

Verifica que diga: `Uvicorn running on http://127.0.0.1:8000`

### 4. Correr el frontend
```bash
npm run dev
```

Abre tu navegador en: **http://localhost:5173**

---

## Las 5 Pantallas

### 🪐 Cargador
- Sliders para ajustar las 15 audio features manualmente
- Toggle **Intragaláctico / Extragaláctico** que recalcula todo en vivo
- Selección de género (salsa, reggaetón, etc.)
- Botón "Analizar en Falkora"

### ✨ Veredicto
- Velocímetro retro animado con el **Gravity Score** (0-100)
- Predicción: **Supernova** (hit), **Rising Star** (mid), o **Dormant Star** (flop)
- Probabilidades de cada clase
- Confianza del modelo

### 🌌 Galaxia
- **Mapa 3D navegable** con Three.js
- Cada estrella es una canción del dataset
- Tu track entra como un **cometa cyan** brillante
- **Drag** para rotar, **Scroll** para zoom
- Hover sobre estrellas para ver nombre/artista/popularidad
- Cambia con el toggle intra/extragaláctico

### 📊 Diagnóstico
- **Radar chart** comparando tu ADN sonoro vs hits del género (o vs todos)
- **Brechas detectadas** — qué features están por debajo/encima
- **Explicación IA** generada por el backend
- **Gravity Score** — qué tan cerca estás del cúmulo de hits

### 👯 Stellar Siblings
- Las 5 canciones **más parecidas** a tu track que sí fueron hits
- Similitud en %, tempo, valence
- Links directos a Spotify para escucharlas
- "Estudia qué hicieron diferente"

---

## El Toggle Intra/Extragaláctico

**🪐 Intragaláctico:** compara tu track solo contra hits de su género.  
Una salsa es "Supernova" si está en el top 10% de las salsas.

**🌍 Extragaláctico:** compara tu track contra todo el universo musical.  
Umbral absoluto de popularidad sin importar género.

Cuando cambias el toggle, **todo se recalcula en vivo:**
- Veredicto cambia
- Gravity Score cambia
- Brechas cambian
- Hermanos sonoros cambian
- Galaxia se reorganiza

---

## Personalización

### Colores
Edita `tailwind.config.js` para cambiar la paleta:
```js
colors: {
  falkora: {
    cyan:   "#05d9e8",  // neón cyan
    pink:   "#ff2d95",  // neón magenta
    purple: "#a855f7",  // neón morado
    // ...
  }
}
```

### Textos
Todos los textos están en los componentes. Por ejemplo, para cambiar el tagline:
- Abre `src/App.jsx`
- Busca `"Where music becomes stars"`
- Cámbialo por lo que quieras

---

## Problemas comunes

### "Cannot connect to backend"
El frontend busca el backend en `http://localhost:8000`. Asegúrate que:
1. El backend esté corriendo (verifica en PowerShell)
2. No haya firewall bloqueando el puerto 8000

### "npm: command not found"
No tienes Node.js instalado. Descarga desde https://nodejs.org/

### La galaxia no se ve
Three.js requiere WebGL. Verifica:
1. Tu navegador soporta WebGL (Chrome/Edge/Firefox modernos sí)
2. Drivers de GPU actualizados

### Errores de CORS
El backend ya tiene CORS configurado para `localhost:5173`. Si cambias el puerto del frontend, actualiza `config.py` en el backend.

---

## Build para producción

Cuando quieras desplegar en un servidor:

```bash
npm run build
```

Eso genera la carpeta `dist/` con HTML/CSS/JS optimizados. Súbelos a cualquier hosting estático (Vercel, Netlify, etc).

---

## Próximos pasos

- [ ] Conectar el upload de WAV (ya está el endpoint `/analyze/upload` en el backend)
- [ ] Agregar autenticación si quieres que sea multi-usuario
- [ ] Mejorar la galaxia con clusters por género visibles
- [ ] Exportar reportes PDF del diagnóstico

---

¿Dudas? Revisa el código — está comentado y organizado. Cada componente hace una cosa clara.

**Enjoy Falkora.** 🌌
