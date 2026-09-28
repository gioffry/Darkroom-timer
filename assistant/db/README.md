# Database catalog maintenance

## Source hierarchy

The user-visible catalog follows one admission rule:

1. **MacoDirect decides what can enter the app.** If a film or chemical is not currently listed by MacoDirect, it is not part of the selectable catalog.
2. **Manufacturer sources provide the preferred technical data** for admitted products.
3. **Digitaltruth/MDC provides specialist film/developer timing data** and is linked to the MacoDirect product through explicit mappings.
4. **Retailer technical data is fallback evidence**, never a substitute for the MacoDirect admission gate.

## Identity rules

- Each commercial product has one canonical row in `catalog_products`.
- Search names belong in `catalog_aliases`.
- An alias means “same product/name”, not “similar formula”.
- Film/developer names used by Digitaltruth are linked through `catalog_specialist_links`.
- Approved timing substitutions remain in `developer_time_equivalents`; they are explicit, one-hop mappings and are not aliases.
- Products that legitimately work for both film and paper carry both roles instead of being duplicated.

## Current maintenance scripts

- `scrape_macodirect_master.py` — crawl the current MacoDirect B&W catalog.
- `build_macodirect_catalog_proposal.py` — build the canonical MacoDirect-gated proposal.
- `apply_macodirect_master_catalog.py` — apply the gated proposal to SQLite.
- `apply_manufacturer_catalog_enrichment.py` — enrich admitted products from manufacturer evidence.
- `apply_macodirect_technical_fallback.py` — apply retailer technical fallback where appropriate.
- `audit_macodirect_gated_db.py` — audit the final gated catalog.
- `test_specialist_link_matrix.py` — regression-check film/developer specialist mappings and approved equivalences.

The APK build remains in `.github/workflows/darkroom-build.yml`. Database refreshes are intentionally not automatic: review the crawl/proposal first, then apply and build a new app version.
