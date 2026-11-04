import {
  Background,
  Controls,
  ReactFlow,
  ReactFlowProvider,
  type Edge,
  type Node,
} from '@xyflow/react'
import { useMemo } from 'react'

import type { GraphSlice } from '../api/types'

type GraphNode = GraphSlice['nodes'][number]
import { isLawyerSafeText } from '../utils/lawyerCopy'
import { IconGraph } from './ui/Icons'

type StaleGraphProps = {
  graph: GraphSlice
}

const STATUS_HINT: Record<string, string> = {
  FOLLOWS: 'meets the requirement',
  RULED_OUT: 'does not meet it',
  UNKNOWN: 'cannot be determined',
  REQUIRES_REVIEW: 'needs your review',
  CONFLICTING: 'readings conflict',
  STALE: 'needs re-check',
  SUPERSEDED: 'superseded',
}

/** The API puts internal status codes in `label`; never show them raw. */
function findingHint(label: string, state: string | null): string {
  if (state === 'STALE') {
    return STATUS_HINT.STALE
  }
  const code = (label ?? '').trim().split(/\s+/).pop() ?? ''
  return STATUS_HINT[code] ?? ''
}

function supportLabel(node: GraphNode): { kind: string; caption: string } {
  if (node.kind === 'rule_card') {
    return { kind: 'Legal test', caption: 'Applied to these answers' }
  }
  if (node.kind === 'provision') {
    return { kind: 'Section', caption: 'Wording that was tested' }
  }
  if (node.kind === 'fact') {
    const label = node.label?.trim() ?? ''
    return {
      kind: 'Fact',
      caption: label && isLawyerSafeText(label) ? label : 'Used in these answers',
    }
  }
  return { kind: 'Law version', caption: 'Recorded source' }
}

const COL_WIDTH = 188
const FINDING_ROW = 84
const SUPPORT_ROW = 78

/**
 * Build the focused graph: the answers that need attention and the chain of
 * law they point at. Showing every finding in the matter makes the map
 * unreadable, so current answers are only a fallback for an all-clear slice.
 */
function buildView(graph: GraphSlice): {
  nodes: Node[]
  edges: Edge[]
  note: string | null
  findingNodes: GraphNode[]
} {
  const findingNodes = graph.nodes.filter((node) => node.kind === 'finding')
  const stale = findingNodes.filter((node) => node.state === 'STALE')
  const shownFindings = stale.length > 0 ? stale : findingNodes.slice(0, 6)
  const note =
    stale.length > 0
      ? 'Showing the answers affected by this change.'
      : findingNodes.length > shownFindings.length
        ? `Showing ${shownFindings.length} of ${findingNodes.length} answers.`
        : null

  const findingIds = new Set(findingNodes.map((node) => node.id))
  const kept = new Set(shownFindings.map((node) => node.id))
  const depth = new Map<string, number>()
  let frontier = new Set(kept)
  for (let level = 1; level <= 3; level += 1) {
    const next = new Set<string>()
    for (const edge of graph.edges) {
      for (const [from, to] of [
        [edge.src, edge.dst],
        [edge.dst, edge.src],
      ] as const) {
        if (frontier.has(from) && !findingIds.has(to) && !kept.has(to)) {
          kept.add(to)
          depth.set(to, level)
          next.add(to)
        }
      }
    }
    frontier = next
    if (next.size === 0) {
      break
    }
  }

  const findings = graph.nodes.filter((node) => shownFindings.some((row) => row.id === node.id))
  const findingsPerRow = Math.max(2, Math.min(4, Math.ceil(Math.sqrt(findings.length || 1))))
  const supportStart = findingsPerRow * COL_WIDTH + 32

  const nodes: Node[] = findings.map((node, index) => {
    return {
      id: node.id,
      data: {
        label: (
          <div className="w-[9.25rem] text-left">
            <div className="text-[0.72rem] font-semibold leading-tight text-ct-ink">Answer</div>
            {findingHint(node.label ?? '', node.state ?? null) ? (
              <div
                className={[
                  'mt-0.5 text-[0.66rem] leading-snug',
                  node.state === 'STALE' ? 'font-medium text-ct-warn' : 'text-ct-muted',
                ].join(' ')}
              >
                {findingHint(node.label ?? '', node.state ?? null)}
              </div>
            ) : null}
          </div>
        ),
      },
      position: {
        x: (index % findingsPerRow) * COL_WIDTH,
        y: Math.floor(index / findingsPerRow) * FINDING_ROW,
      },
      className:
        node.state === 'STALE'
          ? 'rounded-md border-2 border-[rgb(var(--ct-warn))] bg-[rgb(var(--ct-warn-soft))] px-2.5 py-2'
          : 'rounded-md border border-[rgb(var(--ct-line-strong))] bg-[rgb(var(--ct-surface))] px-2.5 py-2',
    }
  })

  const supportColumns = new Map<number, number>()
  for (const node of graph.nodes) {
    if (!kept.has(node.id) || findingIds.has(node.id)) {
      continue
    }
    const level = depth.get(node.id) ?? 1
    const index = supportColumns.get(level) ?? 0
    supportColumns.set(level, index + 1)
    const { kind, caption } = supportLabel(node)
    nodes.push({
      id: node.id,
      data: {
        label: (
          <div className="w-[9.25rem] text-left">
            <div className="text-[0.62rem] uppercase tracking-wide text-ct-faint">{kind}</div>
            <div className="mt-0.5 line-clamp-2 text-[0.7rem] font-medium leading-snug text-ct-ink">
              {caption}
            </div>
          </div>
        ),
      },
      position: {
        x: supportStart + (level - 1) * COL_WIDTH,
        y: index * SUPPORT_ROW,
      },
      className:
        'rounded-md border border-dashed border-[rgb(var(--ct-line-strong))] bg-[rgb(var(--ct-surface-2))] px-2.5 py-2',
    })
  }

  const nodeIds = new Set(nodes.map((node) => node.id))
  const edges: Edge[] = graph.edges
    .filter((edge) => nodeIds.has(edge.src) && nodeIds.has(edge.dst))
    .map((edge) => ({
      id: `${edge.src}-${edge.dst}`,
      source: edge.src,
      target: edge.dst,
      animated: edge.rel === 'DEPENDS_ON',
      style: { stroke: 'rgb(var(--ct-line-strong))', strokeWidth: 1.2 },
    }))

  return { nodes, edges, note, findingNodes }
}

export function StaleGraph({ graph }: StaleGraphProps) {
  const { nodes, edges, note, findingNodes } = useMemo(() => buildView(graph), [graph])
  const staleCount = findingNodes.filter((node) => node.state === 'STALE').length

  return (
    <section className="ct-panel" aria-label="How answers depend on the law">
      <div className="ct-panel-head">
        <div className="flex items-start gap-2.5">
          <span className="mt-0.5 text-ct-muted" aria-hidden="true">
            <IconGraph size={17} />
          </span>
          <div>
            <h2 className="ct-panel-title">Dependency map</h2>
            <p className="ct-panel-desc">
              {staleCount} of {findingNodes.length} answers need re-check
            </p>
            {note ? <p className="ct-panel-desc">{note}</p> : null}
          </div>
        </div>
        <ul
          className="flex flex-wrap items-center gap-3 text-[0.7rem] text-ct-muted"
          aria-label="Legend"
        >
          <li className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-sm border border-ct-lineStrong bg-ct-surface" />
            Answer
          </li>
          <li className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-sm border-2 border-ct-warn bg-ct-warnSoft" />
            Needs re-check
          </li>
          <li className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-sm border border-dashed border-ct-lineStrong bg-ct-surface2" />
            Law or test
          </li>
        </ul>
      </div>
      <div className="h-[320px] border-b border-ct-line bg-ct-surface2">
        <ReactFlowProvider>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            fitView
            fitViewOptions={{ maxZoom: 1.05, minZoom: 0.7, padding: 0.2 }}
            minZoom={0.4}
            nodesConnectable={false}
            elementsSelectable={false}
            proOptions={{ hideAttribution: true }}
          >
            <Background gap={18} size={1} />
            <Controls showInteractive={false} />
          </ReactFlow>
        </ReactFlowProvider>
      </div>
      <ul className="divide-y divide-ct-line lg:hidden">
        {findingNodes.map((node) => (
          <li key={node.id} className="flex items-center justify-between gap-2 px-4 py-2.5 text-sm">
            <span className="text-ct-soft">Answer</span>
            <span
              className={
                node.state === 'STALE'
                  ? 'text-xs font-medium text-ct-warn'
                  : 'text-xs text-ct-muted'
              }
            >
              {node.state === 'STALE' ? 'Needs re-check' : 'Current'}
            </span>
          </li>
        ))}
      </ul>
    </section>
  )
}
