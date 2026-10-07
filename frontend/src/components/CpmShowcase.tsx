/**
 * CpmShowcase — ukážka výpočtu priamo na landing page.
 *
 * Stránka doteraz tvrdila, že Nodus počíta kritickú cestu, ale nikdy ju
 * neukázala. Toto je tá istá sieť, akú dostane každý cez „Ukáž mi to na
 * príklade", vrátane skutočných čísel z CPM: ES/EF, rezervy a kritická cesta.
 *
 * Kreslí sa ako SVG, nie ako snímka obrazovky — ostane ostré na každom
 * displeji, funguje v oboch režimoch a nepribudne pol megabajtu do balíka.
 */

/**
 * Hodnoty tej istej siete, akú zakladá POST /projects/demo.
 *
 * Nie sú odhadnuté — sú odpísané z výstupu CPM motora a stráži ich test
 * `test_showcase_numbers_match_landing_page` v tests/test_demo_project.py.
 * Keď sa zmení DEMO_TASKS v projects_routeri, test spadne a ukáže sem.
 */
const TASKS = [
  { name: 'Zber požiadaviek',  es: 0,  ef: 4,  float: 0,  critical: true },
  { name: 'Návrh riešenia',    es: 4,  ef: 10, float: 0,  critical: true },
  { name: 'Nákup vybavenia',   es: 4,  ef: 7,  float: 10, critical: false },
  { name: 'Implementácia',     es: 10, ef: 19, float: 0,  critical: true },
  { name: 'Zaškolenie',        es: 7,  ef: 9,  float: 10, critical: false },
  { name: 'Odovzdanie',        es: 19, ef: 21, float: 0,  critical: true },
]

const TOTAL_DAYS = 21
// Súradnicový priestor je zámerne úzky. SVG sa škáluje na šírku rodiča — pri
// viewBoxe 480 sa na telefóne (~294 px) zmenšil na 0,6 a deväťbodový text
// vychádzal na 5,5 px. Takto sa zmenší len mierne a popisy ostanú čitateľné.
const VIEW_W = 360
const LABEL_W = 124
const ROW_H = 30
const BAR_H = 17
const TOP = 26
const RIGHT_PAD = 8

export default function CpmShowcase() {
  const width = VIEW_W
  const trackW = width - LABEL_W - RIGHT_PAD
  const dayW = trackW / TOTAL_DAYS
  const height = TOP + TASKS.length * ROW_H + 10

  return (
    <figure className="card p-5 sm:p-6">
      <figcaption className="flex items-baseline justify-between gap-3 mb-4">
        <span className="text-sm font-semibold text-gray-900 dark:text-white">
          Rekonštrukcia pobočky
        </span>
        <span className="text-xs text-gray-400">
          21 dní · kritická cesta cez 4 úlohy
        </span>
      </figcaption>

      <svg
        viewBox={`0 0 ${width} ${height}`}
        /* Strop na šírku — bez neho sa diagram na desktope roztiahol na 1,35×
           a popisy úloh vyšli väčšie než nadpis karty nad nimi. */
        className="w-full max-w-[400px] mx-auto h-auto font-sans"
        role="img"
        aria-label="Ganttov diagram so zvýraznenou kritickou cestou a časovými rezervami"
      >
        {/* mriežka po piatich dňoch */}
        {[0, 5, 10, 15, 20].map(d => (
          <g key={d}>
            <line
              x1={LABEL_W + d * dayW} y1={TOP - 12}
              x2={LABEL_W + d * dayW} y2={height - 10}
              className="stroke-gray-200 dark:stroke-white/10" strokeWidth={1}
            />
            <text
              x={LABEL_W + d * dayW} y={TOP - 17}
              textAnchor="middle" fontSize={10}
              className="fill-gray-400"
            >
              {d}
            </text>
          </g>
        ))}

        {TASKS.map((t, i) => {
          const y = TOP + i * ROW_H
          const x = LABEL_W + t.es * dayW
          const w = Math.max((t.ef - t.es) * dayW, 3)
          return (
            <g key={t.name}>
              <text
                x={LABEL_W - 10} y={y + BAR_H / 2 + 4}
                textAnchor="end" fontSize={11.5}
                className="fill-gray-600 dark:fill-gray-300"
              >
                {t.name}
              </text>

              {/* Rezerva — práve toto konkurencia nezobrazuje.
                  Nad tmavým pozadím musí byť presvetlenejšia, inak z jantárovej
                  pri nízkom krytí vyjde kalná olivová. */}
              {t.float > 0 && (
                <rect
                  x={x + w} y={y + 3} width={t.float * dayW} height={BAR_H - 6}
                  rx={3} className="fill-amber-400/40 dark:fill-amber-300/55"
                />
              )}

              <rect
                x={x} y={y} width={w} height={BAR_H} rx={4}
                className={t.critical ? 'fill-red-500' : 'fill-brand-500'}
              />

              {w > 34 && (
                <text
                  x={x + w / 2} y={y + BAR_H / 2 + 4}
                  textAnchor="middle" fontSize={9.5} fontWeight={600}
                  className="fill-white"
                >
                  {t.es}–{t.ef}
                </text>
              )}
            </g>
          )
        })}
      </svg>

      <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-gray-500 dark:text-gray-400">
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-2.5 rounded-sm bg-red-500" /> Kritická — nemá rezervu
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-2.5 rounded-sm bg-brand-500" /> Bežná úloha
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-2.5 rounded-sm bg-amber-400/60 dark:bg-amber-300/60" /> Časová rezerva
        </span>
      </div>
    </figure>
  )
}
