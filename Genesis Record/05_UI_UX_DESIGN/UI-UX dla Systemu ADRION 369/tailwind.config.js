/**
 * ═══════════════════════════════════════════════════════════════
 * VORTEX-PHI — Tailwind CSS Configuration
 * ═══════════════════════════════════════════════════════════════
 * Matematyka: φ ≈ 1.618 (złoty podział) + 3-6-9 (vortex math)
 * Timing: Częstotliwości Solfeggio (174/396/528 Hz)
 * Użycie: <script src="https://cdn.tailwindcss.com"></script>
 *         <script src="tailwind.config.js"></script>
 *         tailwind.config = vortexPhiConfig;
 * ═══════════════════════════════════════════════════════════════
 */

const vortexPhiConfig = {
  theme: {
    extend: {
      /* ─── TYPOGRAFIA (skala φ) ─── */
      fontSize: {
        'vx-xs':   ['9px',  { lineHeight: '1.618' }],
        'vx-sm':   ['12px', { lineHeight: '1.618' }],
        'vx-base': ['15px', { lineHeight: '1.618' }],
        'vx-md':   ['24px', { lineHeight: '1.3' }],
        'vx-lg':   ['39px', { lineHeight: '1.1' }],
        'vx-xl':   ['63px', { lineHeight: '1.0' }],
      },

      fontFamily: {
        heading: ['Rajdhani', 'Michroma', 'sans-serif'],
        data:    ['JetBrains Mono', 'Space Mono', 'Fira Code', 'monospace'],
        body:    ['Inter', 'Saira', 'sans-serif'],
      },

      /* ─── SPACING (V-Unit = 9px) ─── */
      spacing: {
        'v1':  '9px',
        'v2':  '18px',
        'v4':  '36px',
        'v8':  '72px',
        'v16': '144px',
      },

      /* ─── GRID (Złoty Podział) ─── */
      width: {
        'phi':     '61.8%',
        'phi-inv': '38.2%',
      },

      /* ─── BORDER RADIUS (3-6-9) ─── */
      borderRadius: {
        'vx-sm':  '3px',
        'vx-md':  '6px',
        'vx-lg':  '9px',
        'vx-phi': '1.618rem',
        'vx-2xl': '2rem',
        'vx-3xl': '2.5rem',
      },

      /* ─── COLORS (Vortex-Phi Palette) ─── */
      colors: {
        vx: {
          // Tło (Punkt 9 — dominanta 60%)
          'bg-deep':    '#020408',
          'bg-primary': '#0b0e14',
          'bg-surface': '#0f1117',
          'bg-raised':  '#161b22',

          // Tekst
          'text':       '#e2e8f0',
          'text-dim':   '#94a3b8',
          'text-muted': '#475569',
          'text-dark':  '#272727',

          // Akcenty (Punkt 3 — szok 10%)
          'cyan':       '#00F3FF',
          'amber':      '#FFB800',
          'gold':       '#f59e0b',

          // Marka (Punkt 6 — zaufanie 30%)
          'indigo':     '#6366f1',
          'emerald':    '#10b981',
          'purple':     '#8b5cf6',

          // Statusy (Solfeggio-aligned)
          'success':    '#10b981',
          'warning':    '#f59e0b',
          'error':      '#ef4444',
          'info':       '#6366f1',
        },
      },

      /* ─── SHADOW (Vortex) ─── */
      boxShadow: {
        'vortex':     '0 9px 27px rgba(0, 0, 0, 0.09)',
        'glow-cyan':  '0 0 20px rgba(0, 243, 255, 0.15)',
        'glow-amber': '0 0 20px rgba(245, 158, 11, 0.1)',
        'glow-indigo':'0 0 20px rgba(99, 102, 241, 0.2)',
      },

      /* ─── MOTION (Solfeggio Timing) ─── */
      transitionDuration: {
        'solf-fast':     '174ms',  // 1+7+4=12→3
        'solf-standard': '396ms',  // 3+9+6=18→9
        'solf-emphasis': '528ms',  // 5+2+8=15→6
      },

      transitionTimingFunction: {
        'vortex': 'cubic-bezier(0.4, 0, 0.2, 1)',
      },

      /* ─── ANIMATION ─── */
      animation: {
        'guardian-pulse': 'guardian-pulse 2s infinite',
        'scan':           'scan 2s linear infinite',
      },
      keyframes: {
        'guardian-pulse': {
          '0%':   { boxShadow: '0 0 0 0 rgba(16, 185, 129, 0.4)' },
          '70%':  { boxShadow: '0 0 0 10px rgba(16, 185, 129, 0)' },
          '100%': { boxShadow: '0 0 0 0 rgba(16, 185, 129, 0)' },
        },
        'scan': {
          '0%':   { top: '-50%' },
          '100%': { top: '100%' },
        },
      },

      /* ─── BACKDROP BLUR ─── */
      backdropBlur: {
        'glass': '25px',
        'vault': '30px',
      },
    },
  },
};

// Export for Tailwind CDN inline usage:
// <script>tailwind.config = vortexPhiConfig;</script>
if (typeof module !== 'undefined') {
  module.exports = vortexPhiConfig;
}
