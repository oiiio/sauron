"""
Session management for Sauron with persistent storage
"""
import os
import json
import uuid
import aiosqlite
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path


class SessionManager:
    """Manages session persistence and multiple concurrent sessions"""
    
    def __init__(self, db_path: str = "./data/sauron.db"):
        self.db_path = db_path
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    async def _get_connection(self):
        """Get database connection"""
        return aiosqlite.connect(self.db_path)
    
    async def init_db(self):
        """Initialize database with schema"""
        async with await self._get_connection() as db:
            # Sessions table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    xezbeth_session_id TEXT,
                    level INTEGER NOT NULL,
                    max_attempts INTEGER NOT NULL,
                    mode TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'created',
                    created_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    extracted_password TEXT
                )
            """)
            
            # Attempts table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    attempt_number INTEGER NOT NULL,
                    prompt TEXT NOT NULL,
                    response TEXT NOT NULL,
                    reasoning TEXT,
                    success BOOLEAN NOT NULL DEFAULT 0,
                    timestamp TIMESTAMP NOT NULL,
                    attack_family TEXT,
                    template_id TEXT,
                    strategy TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            """)
            
            # Telemetry table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    attempt_number INTEGER NOT NULL,
                    template_success_rate REAL,
                    template_quality_score REAL,
                    template_relevance_score REAL,
                    family_id TEXT,
                    family_success_rate REAL,
                    family_selection_probability REAL,
                    coverage_percentage REAL,
                    timestamp TIMESTAMP NOT NULL,
                    raw_telemetry TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            """)
            
            # Create indexes for better performance
            await db.execute("CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_attempts_session_id ON attempts(session_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_session_id ON telemetry(session_id)")
            
            await db.commit()
    
    async def create_session(
        self,
        level: int,
        max_attempts: int,
        mode: str,
        xezbeth_session_id: Optional[str] = None
    ) -> str:
        """Create new session"""
        session_id = str(uuid.uuid4())
        
        async with await self._get_connection() as db:
            await db.execute("""
                INSERT INTO sessions (id, xezbeth_session_id, level, max_attempts, mode, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'created', ?)
            """, (session_id, xezbeth_session_id, level, max_attempts, mode, datetime.now()))
            await db.commit()
        
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session details"""
        async with await self._get_connection() as db:
            async with db.execute("""
                SELECT id, xezbeth_session_id, level, max_attempts, mode, status, 
                       created_at, completed_at, extracted_password
                FROM sessions WHERE id = ?
            """, (session_id,)) as cursor:
                row = await cursor.fetchone()
                
                if not row:
                    return None
                
                return {
                    "id": row[0],
                    "xezbeth_session_id": row[1],
                    "level": row[2],
                    "max_attempts": row[3],
                    "mode": row[4],
                    "status": row[5],
                    "created_at": row[6],
                    "completed_at": row[7],
                    "extracted_password": row[8]
                }
    
    async def update_session_status(
        self,
        session_id: str,
        status: str,
        extracted_password: Optional[str] = None
    ):
        """Update session status"""
        async with await self._get_connection() as db:
            if status in ['success', 'failed', 'stopped']:
                await db.execute("""
                    UPDATE sessions 
                    SET status = ?, completed_at = ?, extracted_password = ?
                    WHERE id = ?
                """, (status, datetime.now(), extracted_password, session_id))
            else:
                await db.execute("""
                    UPDATE sessions SET status = ? WHERE id = ?
                """, (status, session_id))
            await db.commit()
    
    async def list_sessions(
        self,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """List all sessions"""
        async with await self._get_connection() as db:
            if status:
                query = """
                    SELECT id, xezbeth_session_id, level, max_attempts, mode, status, 
                           created_at, completed_at, extracted_password
                    FROM sessions WHERE status = ?
                    ORDER BY created_at DESC LIMIT ?
                """
                params = (status, limit)
            else:
                query = """
                    SELECT id, xezbeth_session_id, level, max_attempts, mode, status, 
                           created_at, completed_at, extracted_password
                    FROM sessions
                    ORDER BY created_at DESC LIMIT ?
                """
                params = (limit,)
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                
                return [
                    {
                        "id": row[0],
                        "xezbeth_session_id": row[1],
                        "level": row[2],
                        "max_attempts": row[3],
                        "mode": row[4],
                        "status": row[5],
                        "created_at": row[6],
                        "completed_at": row[7],
                        "extracted_password": row[8]
                    }
                    for row in rows
                ]
    
    async def add_attempt(
        self,
        session_id: str,
        attempt_data: Dict
    ):
        """Add attempt to session"""
        async with await self._get_connection() as db:
            await db.execute("""
                INSERT INTO attempts (
                    session_id, attempt_number, prompt, response, reasoning, 
                    success, timestamp, attack_family, template_id, strategy
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                attempt_data.get("attempt_number"),
                attempt_data.get("prompt"),
                attempt_data.get("response"),
                attempt_data.get("reasoning"),
                attempt_data.get("success", False),
                attempt_data.get("timestamp", datetime.now()),
                attempt_data.get("attack_family"),
                attempt_data.get("template_id"),
                attempt_data.get("strategy")
            ))
            await db.commit()
    
    async def get_attempts(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """Get attempts for a session"""
        async with await self._get_connection() as db:
            if limit:
                query = """
                    SELECT id, session_id, attempt_number, prompt, response, reasoning,
                           success, timestamp, attack_family, template_id, strategy
                    FROM attempts WHERE session_id = ?
                    ORDER BY attempt_number DESC LIMIT ?
                """
                params = (session_id, limit)
            else:
                query = """
                    SELECT id, session_id, attempt_number, prompt, response, reasoning,
                           success, timestamp, attack_family, template_id, strategy
                    FROM attempts WHERE session_id = ?
                    ORDER BY attempt_number DESC
                """
                params = (session_id,)
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                
                return [
                    {
                        "id": row[0],
                        "session_id": row[1],
                        "attempt_number": row[2],
                        "prompt": row[3],
                        "response": row[4],
                        "reasoning": row[5],
                        "success": bool(row[6]),
                        "timestamp": row[7],
                        "attack_family": row[8],
                        "template_id": row[9],
                        "strategy": row[10]
                    }
                    for row in rows
                ]
    
    async def add_telemetry(
        self,
        session_id: str,
        attempt_number: int,
        telemetry_data: Dict
    ):
        """Add telemetry data"""
        async with await self._get_connection() as db:
            await db.execute("""
                INSERT INTO telemetry (
                    session_id, attempt_number, template_success_rate, 
                    template_quality_score, template_relevance_score,
                    family_id, family_success_rate, family_selection_probability,
                    coverage_percentage, timestamp, raw_telemetry
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                attempt_number,
                telemetry_data.get("template_historical_success_rate"),
                telemetry_data.get("template_quality_score"),
                telemetry_data.get("template_relevance_score"),
                telemetry_data.get("attack_family"),
                telemetry_data.get("family_success_rate"),
                telemetry_data.get("family_selection_probability"),
                telemetry_data.get("session_progress", {}).get("coverage_percentage"),
                datetime.now(),
                json.dumps(telemetry_data)
            ))
            await db.commit()
    
    async def get_telemetry(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """Get telemetry data for a session"""
        async with await self._get_connection() as db:
            if limit:
                query = """
                    SELECT * FROM telemetry WHERE session_id = ?
                    ORDER BY attempt_number DESC LIMIT ?
                """
                params = (session_id, limit)
            else:
                query = """
                    SELECT * FROM telemetry WHERE session_id = ?
                    ORDER BY attempt_number DESC
                """
                params = (session_id,)
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                
                return [
                    {
                        "id": row[0],
                        "session_id": row[1],
                        "attempt_number": row[2],
                        "template_success_rate": row[3],
                        "template_quality_score": row[4],
                        "template_relevance_score": row[5],
                        "family_id": row[6],
                        "family_success_rate": row[7],
                        "family_selection_probability": row[8],
                        "coverage_percentage": row[9],
                        "timestamp": row[10],
                        "raw_telemetry": json.loads(row[11]) if row[11] else {}
                    }
                    for row in rows
                ]
    
    async def get_session_stats(self, session_id: str) -> Dict:
        """Get session statistics"""
        async with await self._get_connection() as db:
            # Get attempt stats
            async with db.execute("""
                SELECT COUNT(*) as total_attempts, 
                       SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_attempts
                FROM attempts WHERE session_id = ?
            """, (session_id,)) as cursor:
                row = await cursor.fetchone()
                total_attempts = row[0] if row else 0
                successful_attempts = row[1] if row else 0
            
            # Get latest telemetry
            async with db.execute("""
                SELECT coverage_percentage FROM telemetry 
                WHERE session_id = ? ORDER BY attempt_number DESC LIMIT 1
            """, (session_id,)) as cursor:
                row = await cursor.fetchone()
                coverage_percentage = row[0] if row else 0.0
            
            success_rate = successful_attempts / total_attempts if total_attempts > 0 else 0.0
            
            return {
                "total_attempts": total_attempts,
                "successful_attempts": successful_attempts,
                "success_rate": success_rate,
                "coverage_percentage": coverage_percentage
            }
    
    async def purge_sessions(
        self,
        before_date: Optional[datetime] = None,
        status_filter: Optional[str] = None
    ) -> int:
        """Purge old sessions"""
        if before_date is None:
            # Default: purge sessions older than 30 days
            before_date = datetime.now() - timedelta(days=30)
        
        async with await self._get_connection() as db:
            # Get sessions to purge
            if status_filter:
                query = "SELECT id FROM sessions WHERE created_at < ? AND status = ?"
                params = (before_date, status_filter)
            else:
                query = "SELECT id FROM sessions WHERE created_at < ?"
                params = (before_date,)
            
            async with db.execute(query, params) as cursor:
                session_ids = [row[0] for row in await cursor.fetchall()]
            
            if not session_ids:
                return 0
            
            # Delete related data
            placeholders = ",".join("?" * len(session_ids))
            
            await db.execute(f"DELETE FROM telemetry WHERE session_id IN ({placeholders})", session_ids)
            await db.execute(f"DELETE FROM attempts WHERE session_id IN ({placeholders})", session_ids)
            await db.execute(f"DELETE FROM sessions WHERE id IN ({placeholders})", session_ids)
            
            await db.commit()
            
            return len(session_ids)
    
    async def close(self):
        """Close database connections"""
        # aiosqlite handles connection cleanup automatically
        pass
