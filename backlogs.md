## Short-Term Milestones

1. Normalize roles, validate inputs, fix response shape (quick wins).
2. Implement history trimming + last-AI logic.
3. Make `/chat` async end-to-end.
4. Tune retrieval + deduplication + pre-formatting.
5. Add streaming endpoint.
6. Improve observability + caching.

---

## Performance / Efficiency

1. **Make everything async end-to-end**
   My FastAPI handlers (`/chat`, `/initialize`) are still sync, which means slow LLM/vector calls block concurrency.

   * Convert them to `async def`.
   * Use `await graph.ainvoke(...)` or async APIs where possible.
   * If some libs don’t support async yet, wrap them in a threadpool and leave TODOs.
     **Goal:** concurrent requests aren’t blocked by slow responses.

2. **Trim conversation history**
   Right now, I pass the full conversation to the LLM every time, which is wasteful.

   * Add a `history_window` (default 10).
   * If history exceeds the limit, summarize old messages into a `system` message.
     **Goal:** keep token usage under control and reduce latency.

3. **Tune retrieval (k, namespace, dedupe)**
   My retrieval step just runs a similarity search with defaults.

   * Add `k` and `namespace` options.
   * Deduplicate sources and collapse repeated docs.
     **Goal:** feed the LLM a tighter, higher-quality context.

4. **Stream responses**
   Right now users wait until the whole LLM reply finishes.

   * Add `/chat/stream` using SSE + `graph.stream(...)` (or `astream`).
   * Keep the existing `/chat` for simpler clients.
     **Goal:** users see tokens as they’re generated for faster perceived latency.

5. **Cache hot paths**
   Some repeated queries hit the vector store + LLM over and over.

   * Add an opt-in cache (LRU in dev, maybe Redis in prod).
   * Cache exact prompts with TTL.
     **Goal:** save cost/latency on identical queries.

6. **Pre-format retrieved context**
   Retrieved chunks can be messy and long.

   * Strip markdown, normalize whitespace.
   * Truncate chunks to a max length (e.g. 1000 chars).
     **Goal:** keep prompts lean and clean.

---

## Stability / Robustness

1. **Defensive startup**
   If graph compilation fails, I should return `503` instead of `500`.

   * Move the “Graph compiled successfully” log to before the `yield`.
   * Mark `app.state.ready = False` on failure, and check readiness in `/chat`.
     **Goal:** clients clearly see when the app isn’t ready.

2. **Timeouts & retries**
   My LLM/vector calls don’t have explicit timeouts or retries.

   * Add config-driven timeouts.
   * Add simple retries with jitter for transient errors.
     **Goal:** fail gracefully instead of hanging forever.

3. **Normalize roles early**
   I need to enforce role validation before hitting the graph.

   * Map incoming `role` → LangChain types (`user→human`, `assistant→ai`, `system→system`).
   * Reject anything unknown with 400.
     **Goal:** consistent, predictable role handling.

4. **Cap request size**
   Right now, someone could send an enormous payload.

   * Limit number of messages (e.g. 50) and total input chars.
   * Reject with 400 or 413 if exceeded.
     **Goal:** prevent OOM and runaway token costs.

---

## Security

1. **Lock down CORS & add simple auth**
   Currently `ALLOWED_ORIGINS` defaults to `*`, which is unsafe.

   * Restrict origins in prod via env var.
   * Add optional API key middleware for basic auth/rate limiting.
     **Goal:** keep the API safe from abuse.

2. **Prompt-injection mitigations**
   Retrieved docs could contain malicious instructions.

   * Add a system instruction that the model should ignore embedded commands.
   * Optionally strip suspicious patterns like code blocks or tool calls.
     **Goal:** reduce risk of prompt injection.

3. **Handle PII in checkpoints**
   Checkpoints might contain sensitive data.

   * Document how to enable `LANGGRAPH_AES_KEY` for encrypted serialization.
     **Goal:** give users a clear path to protect sensitive data.

---

## Observability

1. **Structured logging with request id**
   Current logs don’t have request scoping or useful metrics.

   * Add a UUID per request.
   * Include it in logs and return it in responses.
   * Log retrieval latency, LLM latency, token counts.
     **Goal:** make it easy to trace and debug issues.

---

## DB / Ops

1. **Checkpoint retention policy**
   My checkpoint table will just grow forever.

   * Add a cleanup job to keep only the last N checkpoints per thread.
     **Goal:** prevent unbounded DB growth.

---

## API Ergonomics / Correctness

1. **Fix response shape & last-AI logic**
   Right now I return `{"messages": last_message.content}`, which is confusing.

   * Decide between `{"message": ...}` or `{"messages": [ ... ]}` and stick to it.
   * Implement a helper that returns the last AI message (fallback: last message).
     **Goal:** clear, consistent API responses.

2. **Make `/initialize` idempotent**
   Re-running ingestion can create duplicates.

   * Upsert or delete-and-insert by `source`.
     **Goal:** no duplicate vectors on repeated runs.

3. **Input validation (roles, sizes)**
   Consolidate role mapping and request size checks into request validation.
   **Goal:** fail fast with clean errors instead of deep stack traces.