export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        falkora: {
          bg:      "#0a0118",
          bg2:     "#150829",
          panel:   "#1a0f2e",
          cyan:    "#05d9e8",
          pink:    "#ff2d95",
          purple:  "#a855f7",
          yellow:  "#f9c80e",
          green:   "#39ff6a",
          red:     "#ff3864",
          text:    "#e8e3ff",
          dim:     "#9d8bc4",
        }
      },
      fontFamily: {
        display: ['Orbitron', 'sans-serif'],
        body:    ['Space Grotesk', 'sans-serif'],
      },
      animation: {
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        'float':      'float 6s ease-in-out infinite',
        'spin-slow':  'spin 20s linear infinite',
      },
      keyframes: {
        pulseGlow: {
          '0%, 100%': { opacity: 1, filter: 'brightness(1)' },
          '50%':      { opacity: 0.8, filter: 'brightness(1.3)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%':      { transform: 'translateY(-12px)' },
        }
      }
    },
  },
  plugins: [],
}
