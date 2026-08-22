# Database enrichment hierarchy

Authoritative hierarchy for Darkroom Assistant developer data:

1. Import Massive Dev Chart data into our SQLite database.
2. Preserve every non-empty MDC value.
3. For each empty technical field, enrich only from official manufacturer documentation.
4. Never overwrite a populated MDC field with manufacturer data unless a future explicit migration rule says so.
5. Never infer or invent a value. Unknown remains NULL/empty with provenance status.

The final product is one enriched database, not parallel MDC/manufacturer databases.

Fields to audit/enrich per developer include: manufacturer, canonical name, aliases, physical state, stock/preparation instructions, supported dilutions, reuse model, capacity, concentrate shelf life, stock shelf life, working-solution shelf life, opened-container life, storage notes, exhaustion notes, source URL/title/date, and per-field provenance.

Massive Dev Chart remains authoritative for film/developer combinations and the fields it supplies there. Manufacturer documentation fills gaps only.