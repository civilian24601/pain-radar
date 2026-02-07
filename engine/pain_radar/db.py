"""SQLite database setup and operations for Pain Radar."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    idea_text TEXT NOT NULL,
    options_json TEXT,
    status TEXT NOT NULL DEFAULT 'created',
    progress_json TEXT,
    clarification_questions_json TEXT,
    clarification_answers_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS source_snapshots (
    content_hash TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    storage_path TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL REFERENCES jobs(id),
    url TEXT NOT NULL,
    excerpt TEXT NOT NULL,
    source_type TEXT NOT NULL,
    date_published TEXT,
    date_retrieved TEXT NOT NULL,
    recency_months INTEGER,
    snapshot_hash TEXT REFERENCES source_snapshots(content_hash)
);

CREATE TABLE IF NOT EXISTS reports (
    job_id TEXT PRIMARY KEY REFERENCES jobs(id),
    report_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_citations_job_id ON citations(job_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_url ON source_snapshots(url);
"""


class Database:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(str(self._db_path))
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(SCHEMA_SQL)
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._db.execute("PRAGMA foreign_keys=ON")
        await self._db.commit()

    async def close(self) -> None:
        if self._db:
            await self._db.close()

    @property
    def db(self) -> aiosqlite.Connection:
        assert self._db is not None, "Database not connected"
        return self._db

    # -- Jobs --

    async def create_job(
        self, job_id: str, idea_text: str, options: dict | None = None
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        await self.db.execute(
            "INSERT INTO jobs (id, idea_text, options_json, status, created_at, updated_at) "
            "VALUES (?, ?, ?, 'created', ?, ?)",
            (job_id, idea_text, json.dumps(options) if options else None, now, now),
        )
        await self.db.commit()

    async def update_job_status(self, job_id: str, status: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        await self.db.execute(
            "UPDATE jobs SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, job_id),
        )
        await self.db.commit()

    async def update_job_progress(self, job_id: str, progress: dict) -> None:
        now = datetime.now(timezone.utc).isoformat()
        await self.db.execute(
            "UPDATE jobs SET progress_json = ?, updated_at = ? WHERE id = ?",
            (json.dumps(progress), now, job_id),
        )
        await self.db.commit()

    async def set_clarification_questions(
        self, job_id: str, questions: list[dict]
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        await self.db.execute(
            "UPDATE jobs SET clarification_questions_json = ?, status = 'clarifying', "
            "updated_at = ? WHERE id = ?",
            (json.dumps(questions), now, job_id),
        )
        await self.db.commit()

    async def set_clarification_answers(
        self, job_id: str, answers: list[dict]
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        await self.db.execute(
            "UPDATE jobs SET clarification_answers_json = ?, updated_at = ? WHERE id = ?",
            (json.dumps(answers), now, job_id),
        )
        await self.db.commit()

    async def get_job(self, job_id: str) -> dict | None:
        cursor = await self.db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    # -- Source Snapshots --

    async def store_snapshot(
        self,
        content_hash: str,
        url: str,
        raw_text: str,
        fetched_at: str,
        storage_path: str,
    ) -> None:
        await self.db.execute(
            "INSERT OR IGNORE INTO source_snapshots "
            "(content_hash, url, raw_text, fetched_at, storage_path) "
            "VALUES (?, ?, ?, ?, ?)",
            (content_hash, url, raw_text, fetched_at, storage_path),
        )
        await self.db.commit()

    async def get_snapshot(self, content_hash: str) -> dict | None:
        cursor = await self.db.execute(
            "SELECT * FROM source_snapshots WHERE content_hash = ?", (content_hash,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_snapshots_for_job(self, job_id: str) -> list[dict]:
        """Get all snapshots referenced by citations for a job."""
        cursor = await self.db.execute(
            "SELECT DISTINCT s.content_hash, s.raw_text FROM source_snapshots s "
            "INNER JOIN citations c ON c.snapshot_hash = s.content_hash "
            "WHERE c.job_id = ?",
            (job_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    # -- Citations --

    async def store_citation(
        self,
        job_id: str,
        url: str,
        excerpt: str,
        source_type: str,
        date_published: str | None,
        date_retrieved: str,
        recency_months: int | None,
        snapshot_hash: str,
    ) -> int:
        cursor = await self.db.execute(
            "INSERT INTO citations "
            "(job_id, url, excerpt, source_type, date_published, date_retrieved, "
            "recency_months, snapshot_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                job_id, url, excerpt, source_type, date_published,
                date_retrieved, recency_months, snapshot_hash,
            ),
        )
        await self.db.commit()
        return cursor.lastrowid  # type: ignore[return-value]

    async def get_citations(self, job_id: str) -> list[dict]:
        cursor = await self.db.execute(
            "SELECT * FROM citations WHERE job_id = ? ORDER BY id", (job_id,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    # -- Reports --

    async def store_report(self, job_id: str, report_json: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        await self.db.execute(
            "INSERT OR REPLACE INTO reports (job_id, report_json, created_at) "
            "VALUES (?, ?, ?)",
            (job_id, report_json, now),
        )
        await self.db.commit()

    async def get_report(self, job_id: str) -> dict | None:
        cursor = await self.db.execute(
            "SELECT * FROM reports WHERE job_id = ?", (job_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
