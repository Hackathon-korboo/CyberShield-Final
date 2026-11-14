# PART 02: BACKEND ARCHITECTURE PLANNING — ISSUES AND FIXES

## Identified Design Challenges & Technical Solutions

### Challenge 1: Risk of Event Loop Starvation by Synchronous Heuristic / Web3 Calls
- **Issue:** Deep regex evaluations or synchronous RPC queries could block FastAPI's asyncio event loop, degrading API concurrency.
- **Resolution:** Architecture requires non-blocking execution: regex heuristics must be linear-time ($O(N)$) and optimized, while any blocking external I/O (Web3 RPC or LLM calls) must use native asynchronous clients (`httpx.AsyncClient`, `AsyncWeb3`) or run in thread pools.

### Challenge 2: Accidental Premature Feature Implementation
- **Issue:** Risk of inadvertently implementing Phase 02 security engine rules or Phase 03 AI calls during architecture design.
- **Resolution:** Maintained strict discipline. The specifications define data structures, boundaries, and interfaces, while deferring all engine logic to their designated future phases.
