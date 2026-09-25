/** @type {import('tailwindcss').Config} */
import colors from 'tailwindcss/colors'
import plugin from 'tailwindcss/plugin'

// Dark mode without a `dark:` variant on every class: each colour the app uses is a CSS
// variable, and dark mode mirrors its scale. A light chip (bg-emerald-100 text-emerald-700)
// becomes a dark one (emerald-900 background, emerald-200 text); a white card on a slate-50
// page becomes slate-900 on slate-950. Components stay written for light mode only.
const HUES = ['slate', 'emerald', 'amber', 'indigo', 'red', 'rose', 'sky', 'orange', 'purple']
const SHADES = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950]
// Not an exact mirror, in two places:
// - 100 -> 800, not 900: the card surface is slate-900, so tinted fills (chips, bar tracks)
//   would otherwise vanish into the card
// - 400 and 500 swap: muted text (slate-400) would otherwise become slate-600, too dim to
//   read on a dark card
const MIRROR = { 50: 950, 100: 800, 200: 800, 300: 700, 400: 500, 500: 400,
                 600: 300, 700: 200, 800: 100, 900: 50, 950: 50 }

const channels = (hex) => {
  const n = parseInt(hex.slice(1), 16)
  return `${n >> 16} ${(n >> 8) & 255} ${n & 255}`
}

const themed = Object.fromEntries(HUES.map((h) => [h, Object.fromEntries(
  SHADES.map((s) => [s, `rgb(var(--c-${h}-${s}) / <alpha-value>)`]),
)]))

function palette(dark) {
  const vars = {}
  for (const h of HUES) {
    for (const s of SHADES) vars[`--c-${h}-${s}`] = channels(colors[h][dark ? MIRROR[s] : s])
  }
  // "white" is the card surface: slate-900 in the dark, one step above the slate-950 page
  vars['--c-white'] = dark ? channels(colors.slate[900]) : '255 255 255'
  return vars
}

export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: { ...themed, white: 'rgb(var(--c-white) / <alpha-value>)' },
    },
  },
  plugins: [
    plugin(({ addBase }) => addBase({
      ':root': palette(false),
      // color-scheme also darkens native widgets: inputs, selects, scrollbars, the datalist
      '.dark': { ...palette(true), colorScheme: 'dark' },
    })),
  ],
}
