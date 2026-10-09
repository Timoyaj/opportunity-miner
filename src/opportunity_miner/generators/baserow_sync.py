"""Baserow / NocoDB CRM sync — 100% FREE OSS Airtable alternatives (MIT).

Baserow: https://github.com/bram2w/baserow (MIT) — `docker run -p 3000:3000 baserow/baserow`
NocoDB:  https://github.com/nocodb/nocodb (AGPL) — `docker run -p 8080:8080 nocodb/nocodb`
Grist:   https://github.com/gristlabs/grist-core (Apache-2.0)

All self-hostable, no per-seat fee. This module pushes OpportunityMiner
opportunities as rows so founders can Kanban-manage pipeline for free.
Fallback: also supports CSV export (zero-deps) if no CRM configured.

Env:
  BASEROW_URL        = http://localhost:3000
  BASEROW_TOKEN      = <API token from Baserow settings>
  BASEROW_TABLE_ID   = <numeric table id>
  NOCODB_URL / NOCODB_TOKEN / NOCODB_TABLE_ID (same pattern)
  CRM_PROVIDER       = baserow | nocodb | grist | csv | auto
"""

import csv
import logging
import os
from pathlib import Path
from datetime import datetime

import requests

logger = logging.getLogger(__name__)


class FreeCrmSync:
    """Push opportunities to Baserow / NocoDB / Grist or CSV (all free OSS)."""

    def __init__(
        self,
        provider: str | None = None,
        baserow_url: str | None = None,
        baserow_token: str | None = None,
        baserow_table_id: str | None = None,
    ):
        self.provider = (provider or os.environ.get("CRM_PROVIDER") or "auto").lower()
        self.baserow_url = (baserow_url or os.environ.get("BASEROW_URL") or "http://localhost:3000").rstrip("/")
        self.baserow_token = baserow_token or os.environ.get("BASEROW_TOKEN") or ""
        self.baserow_table_id = baserow_table_id or os.environ.get("BASEROW_TABLE_ID") or ""

        self.nocodb_url = os.environ.get("NOCODB_URL") or ""
        self.nocodb_token = os.environ.get("NOCODB_TOKEN") or ""
        self.nocodb_table_id = os.environ.get("NOCODB_TABLE_ID") or ""

    def _push_baserow(self, payload: dict) -> bool:
        if not self.baserow_token or not self.baserow_table_id:
            logger.debug("Baserow token/table not set — skip (set BASEROW_TOKEN, BASEROW_TABLE_ID)")
            return False
        try:
            resp = requests.post(
                f"{self.baserow_url}/api/database/rows/table/{self.baserow_table_id}/?user_field_names=true",
                headers={"Authorization": f"Token {self.baserow_token}", "Content-Type": "application/json"},
                json=payload,
                timeout=8,
            )
            if resp.status_code in (200, 201):
                return True
            logger.warning(f"Baserow push failed {resp.status_code}: {resp.text[:300]}")
            return False
        except Exception as e:
            logger.warning(f"Baserow push error: {e}")
            return False

    def _push_nocodb(self, payload: dict) -> bool:
        if not self.nocodb_token or not self.nocodb_table_id:
            logger.debug("NocoDB token/table not set — skip (set NOCODB_TOKEN, NOCODB_TABLE_ID)")
            return False
        try:
            # NocoDB v2 API: POST /api/v2/tables/{tableId}/records
            resp = requests.post(
                f"{self.nocodb_url.rstrip('/')}/api/v2/tables/{self.nocodb_table_id}/records",
                headers={"xc-token": self.nocodb_token, "Content-Type": "application/json"},
                json=payload,
                timeout=8,
            )
            if resp.status_code in (200, 201):
                return True
            logger.warning(f"NocoDB push failed {resp.status_code}: {resp.text[:300]}")
            return False
        except Exception as e:
            logger.warning(f"NocoDB push error: {e}")
            return False

    def _push_csv(self, payload: dict, csv_path: str = "data/crm_export.csv") -> bool:
        try:
            p = Path(csv_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            write_header = not p.exists()
            with open(p, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(payload.keys()))
                if write_header:
                    writer.writeheader()
                writer.writerow(payload)
            return True
        except Exception as e:
            logger.warning(f"CSV export failed: {e}")
            return False

    def push_opportunity(self, opportunity) -> dict[str, bool]:
        """Push a single Opportunity (SQLAlchemy) to configured free CRM(s)."""
        # Normalize ORM object to flat dict for any CRM
        payload = {
            "id": getattr(opportunity, "id", ""),
            "title": getattr(opportunity, "title", ""),
            "category": getattr(opportunity, "category", ""),
            "score": int(getattr(opportunity, "opportunity_score", 0) or 0),
            "confidence": float(getattr(opportunity, "confidence_score", 0) or 0),
            "evidence_level": int(getattr(opportunity, "evidence_level", 1) or 1),
            "status": getattr(opportunity, "status", "NEW"),
            "created_at": datetime.utcnow().isoformat(),
        }
        # Add score breakdown as flat fields for Kanban filtering
        try:
            bd = getattr(opportunity, "score_breakdown", {}) or {}
            for k, v in bd.items():
                payload[f"score_{k}"] = v
        except Exception:
            pass

        results: dict[str, bool] = {}

        if self.provider in ("baserow", "auto") and self.baserow_token:
            results["baserow"] = self._push_baserow(payload)
        if self.provider in ("nocodb", "auto") and self.nocodb_token:
            results["nocodb"] = self._push_nocodb(payload)
        if self.provider in ("csv", "auto") or not results:
            # Always ensure CSV fallback works (zero-deps, local file)
            results["csv"] = self._push_csv(payload)

        if self.provider == "auto" and not any([self.baserow_token, self.nocodb_token]):
            logger.info("FreeCrmSync: no Baserow/NocoDB configured — wrote to data/crm_export.csv (free fallback). Set BASEROW_TOKEN to enable Baserow (MIT).")

        return results
