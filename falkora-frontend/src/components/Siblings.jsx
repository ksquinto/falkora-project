import { motion } from 'framer-motion'

/*
  Siblings — Stellar Siblings. Las canciones-hit más parecidas.
  Link a Spotify (no embed, solo enlace por simplicidad).
*/
export default function Siblings({ siblings = [] }) {
  if (!siblings.length) return null

  return (
    <div>
      <h3 className="font-display text-falkora-cyan text-center text-sm tracking-widest mb-2 uppercase">
        ◢ Stellar Siblings — Hits más parecidos a tu track
      </h3>
      <p className="text-center text-falkora-dim text-xs mb-6">
        Estas canciones comparten tu ADN sonoro pero alcanzaron el éxito. Estúdialas.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {siblings.map((s, i) => (
          <motion.a
            key={s.id || i}
            href={`https://open.spotify.com/track/${s.id}`}
            target="_blank"
            rel="noopener noreferrer"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="panel-card p-5 block hover:scale-[1.03] transition-transform cursor-pointer group"
            style={{ textDecoration: 'none' }}>
            <div className="flex justify-between items-start mb-2">
              <span className="text-falkora-green text-xs tracking-wide">
                {s.similarity}% similar
              </span>
              <span className="text-falkora-dim text-xs group-hover:text-falkora-cyan transition-colors">
                ▶ Spotify
              </span>
            </div>
            <div className="font-bold text-base text-falkora-text mb-1 leading-tight">
              {s.name}
            </div>
            <div className="text-falkora-dim text-xs mb-3">{s.artist}</div>
            <div className="flex justify-between text-xs pt-3 border-t border-falkora-purple/20">
              <span className="text-falkora-yellow">Pop {s.popularity} 🌟</span>
              <span className="text-falkora-dim">{Math.round(s.tempo)} BPM</span>
              <span className="text-falkora-dim">val {s.valence}</span>
            </div>
          </motion.a>
        ))}
      </div>
    </div>
  )
}
