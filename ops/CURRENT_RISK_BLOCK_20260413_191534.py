# ===== RISK DASHBOARD API (FIXED) =====

@app.get("/api/risk/entities")
async def api_risk_entities():
    async with get_pg_conn() as conn:
        rows = await conn.fetch("""
            SELECT
                entity_id,
                canonical_name,
                score_zuz,
                approved_reports,
                verified_evidence,
                eligible_for_publication
            FROM v_risk_entity_score
            ORDER BY score_zuz DESC, canonical_name
        """)

        items = [{
            "entity_id": r["entity_id"],
            "canonical_name": r["canonical_name"],
            "score_zuz": float(r["score_zuz"] or 0),
            "approved_reports": int(r["approved_reports"] or 0),
            "verified_evidence": int(r["verified_evidence"] or 0),
            "eligible_for_publication": bool(r["eligible_for_publication"])
        } for r in rows]

        return {
            "ok": True,
            "total_entities": len(items),
            "public_ready": sum(1 for x in items if x["eligible_for_publication"]),
            "items": items
        }


@app.get("/api/risk/external-watch")
async def api_external_watch():
    async with get_pg_conn() as conn:
        rows = await conn.fetch("""
            SELECT
                w.asset_key,
                w.asset_name,
                w.chain,
                w.contract_address,
                s.price_usd,
                s.observed_at
            FROM external_asset_watch w
            LEFT JOIN LATERAL (
                SELECT price_usd, observed_at
                FROM external_asset_snapshots
                WHERE asset_key = w.asset_key
                ORDER BY observed_at DESC
                LIMIT 1
            ) s ON TRUE
            ORDER BY w.asset_name
        """)

        items = [{
            "asset_key": r["asset_key"],
            "asset_name": r["asset_name"],
            "chain": r["chain"],
            "contract_address": r["contract_address"],
            "last_price_usd": float(r["price_usd"]) if r["price_usd"] is not None else None,
            "last_seen_at": r["observed_at"].isoformat() if r["observed_at"] else None
        } for r in rows]

        return {
            "ok": True,
            "total_assets": len(items),
            "items": items
        }

# ===== END RISK DASHBOARD API (FIXED) =====
