import type uPlot from 'uplot'

export function isDarkMode(): boolean {
  return document.documentElement.classList.contains('dark')
}

export function chartColors(): { grid: string; line: string; text: string; fill: string } {
  const dark = isDarkMode()
  return {
    grid: dark ? '#262626' : '#e5e5e5',
    line: dark ? '#3b82f6' : '#2563eb',
    text: dark ? '#a3a3a3' : '#737373',
    fill: dark ? 'rgba(59,130,246,0.12)' : 'rgba(37,99,235,0.12)',
  }
}

export function baseUPlotOpts(width: number, height: number): Partial<uPlot.Options> {
  const colors = chartColors()
  return {
    width,
    height,
    scales: {
      x: { time: true },
      y: { auto: true },
    },
    axes: [
      {
        stroke: colors.text,
        grid: { stroke: colors.grid },
        ticks: { stroke: colors.grid },
        font: '11px sans-serif',
      },
      {
        stroke: colors.text,
        grid: { stroke: colors.grid },
        ticks: { stroke: colors.grid },
        font: '11px sans-serif',
        size: 48,
      },
    ],
    series: [
      {},
      {
        stroke: colors.line,
        width: 2,
        fill: colors.fill,
        points: { show: true, size: 5, stroke: colors.line, fill: colors.line },
      },
    ],
    cursor: {
      drag: { x: true, y: false, setScale: true },
      points: { show: true },
    },
    legend: { show: false },
  }
}
