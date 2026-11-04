"""Verification domain: ask, proof drafting, status decisions.

Owns: the agent loop over the six bounded tools, the deterministic
checker boundary, the challenger second pass, and — exclusively — the
memory service that decides finding status. No other domain may write a
finding status; this facade is the only public entry to that decision.

Public interface: `run_verify` (agent loop, in app.agent), `decide_finding`
(memory). Forbidden: importing the HTTP layer; letting model output set
a status.
"""

import app.modules.verification.memory as memory
from app.agent import loop as agent_loop
from app.agent import tools

__all__ = ["agent_loop", "tools", "memory"]
