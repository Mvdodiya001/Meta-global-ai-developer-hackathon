import type { ReactNode } from 'react'

import { Panel } from './Panel'

type QueueListProps = {
  heading: string
  headingId: string
  emptyText: string
  isEmpty: boolean
  children: ReactNode
  description?: ReactNode
  actions?: ReactNode
}

/** A named work queue with an explicit empty state (P4). */
export function QueueList({
  heading,
  headingId,
  emptyText,
  isEmpty,
  children,
  description,
  actions,
}: QueueListProps) {
  return (
    <Panel
      heading={heading}
      headingId={headingId}
      description={description}
      actions={actions}
    >
      {isEmpty ? <p className="ct-empty">{emptyText}</p> : <ul className="ct-rows">{children}</ul>}
    </Panel>
  )
}
