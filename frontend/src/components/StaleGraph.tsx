import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  type Edge,
  type Node,
} from '@xyflow/react'
import { useMemo } from 'react'

import type { GraphSlice } from '../api/types'

type StaleGraphProps = {
  graph: GraphSlice
}

function toFlowGraph(slice: GraphSlice): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = slice.nodes.map((node, index) => ({
    id: node.id,
    data: {
      label: (
        <div className="text-xs">
          <div className="font-semibold">{node.label}</div>
          <div className="text-slate-500">{node.kind}</div>
          {node.state ? (
            <div className="mt-1 font-medium text-orange-700">{node.state}</div>
          ) : null}
        </div>
      ),
    },
    position: { x: index * 220, y: node.kind === 'finding' ? 0 : 120 },
    className:
      node.state === 'STALE'
        ? 'rounded-md border-2 border-orange-500 bg-orange-50 px-2 py-1 dark:bg-orange-950/30'
        : 'rounded-md border border-slate-300 bg-white px-2 py-1 dark:border-slate-600 dark:bg-slate-900',
  }))

  const edges: Edge[] = slice.edges.map((edge) => ({
    id: `${edge.src}-${edge.dst}`,
    source: edge.src,
    target: edge.dst,
    label: edge.rel,
    animated: edge.rel === 'DEPENDS_ON',
  }))

  return { nodes, edges }
}

export function StaleGraph({ graph }: StaleGraphProps) {
  const { nodes, edges } = useMemo(() => toFlowGraph(graph), [graph])

  return (
    <section className="ct-panel h-[320px] overflow-hidden" aria-label="Dependency graph">
      <ReactFlowProvider>
        <ReactFlow nodes={nodes} edges={edges} fitView proOptions={{ hideAttribution: true }}>
          <Background gap={16} />
          <MiniMap pannable zoomable />
          <Controls showInteractive={false} />
        </ReactFlow>
      </ReactFlowProvider>
    </section>
  )
}
