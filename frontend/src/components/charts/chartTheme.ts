import type uPlot from 'uplot'
import uPlotLib from 'uplot'

function cssVar(name: string, fallback: string): string {
  if (typeof document === 'undefined') return fallback
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return value || fallback
}

export function isDarkMode(): boolean {
  return document.documentElement.classList.contains('dark')
}

export function chartColors(): { grid: string; line: string; text: string; fill: string } {
  return {
    grid: cssVar('--chart-grid', '#e5e5e5'),
    line: cssVar('--chart-line', '#2563eb'),
    text: cssVar('--text-secondary', '#737373'),
    fill: cssVar('--chart-fill', 'rgba(37, 99, 235, 0.12)'),
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
        spanGaps: false,
        paths: uPlotLib.paths.linear?.(),
        points: { show: true, size: 6, stroke: colors.line, fill: colors.line },
      },
    ],
    cursor: {
      show: true,
      x: true,
      y: false,
      drag: { x: true, y: false, setScale: true },
      points: { show: true, size: 6, stroke: colors.line, fill: colors.line },
    },
    legend: { show: false },
  }
}
