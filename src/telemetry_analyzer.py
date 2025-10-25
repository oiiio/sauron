"""
Advanced telemetry analysis for Xezbeth data
"""
import json
import sqlite3
from typing import Dict, List, Optional, Any, Tuple, DefaultDict
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict, Counter
import statistics
import re


@dataclass
class AttackFamilyStats:
    """Statistics for an attack family"""
    family_id: str
    total_attempts: int
    successful_attempts: int
    success_rate: float
    avg_template_quality: float
    avg_relevance_score: float
    levels_used: List[int]
    recent_success_rate: float  # Last 30 days
    trend: str  # "improving", "declining", "stable"


@dataclass
class TemplateStats:
    """Statistics for a specific template"""
    template_id: str
    attack_family: str
    total_uses: int
    successful_uses: int
    success_rate: float
    avg_quality_score: float
    avg_relevance_score: float
    levels_effective: List[int]
    last_used: datetime
    effectiveness_trend: str


@dataclass
class LevelAnalysis:
    """Analysis for a specific Gandalf level"""
    level: int
    total_sessions: int
    successful_sessions: int
    success_rate: float
    avg_attempts_to_success: float
    most_effective_families: List[Tuple[str, float]]
    most_effective_templates: List[Tuple[str, float]]
    common_failure_patterns: List[str]
    avg_session_duration: float


@dataclass
class SessionPattern:
    """Pattern identified in session data"""
    pattern_type: str  # "success_sequence", "failure_loop", "breakthrough"
    description: str
    frequency: int
    success_correlation: float
    example_sessions: List[str]


class TelemetryAnalyzer:
    """Advanced analysis of Xezbeth telemetry data"""
    
    def __init__(self, db_path: str = "./data/sauron.db"):
        self.db_path = db_path
    
    def _get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    async def get_attack_family_stats(
        self,
        days_back: Optional[int] = None,
        level_filter: Optional[int] = None
    ) -> List[AttackFamilyStats]:
        """Get comprehensive statistics for all attack families"""
        
        with self._get_connection() as conn:
            # Base query
            query = """
                SELECT 
                    t.family_id,
                    COUNT(*) as total_attempts,
                    SUM(CASE WHEN a.success = 1 THEN 1 ELSE 0 END) as successful_attempts,
                    AVG(t.template_quality_score) as avg_quality,
                    AVG(t.template_relevance_score) as avg_relevance,
                    s.level,
                    t.timestamp
                FROM telemetry t
                JOIN attempts a ON t.session_id = a.session_id AND t.attempt_number = a.attempt_number
                JOIN sessions s ON t.session_id = s.id
                WHERE t.family_id IS NOT NULL
            """
            
            params = []
            if days_back:
                query += " AND t.timestamp >= ?"
                params.append(datetime.now() - timedelta(days=days_back))
            
            if level_filter:
                query += " AND s.level = ?"
                params.append(level_filter)
            
            query += " GROUP BY t.family_id, s.level ORDER BY t.family_id"
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            # Aggregate by family
            family_data: DefaultDict[str, Dict[str, Any]] = defaultdict(lambda: {
                'total_attempts': 0,
                'successful_attempts': 0,
                'quality_scores': [],
                'relevance_scores': [],
                'levels': set(),
                'recent_attempts': 0,
                'recent_successes': 0
            })
            
            recent_cutoff = datetime.now() - timedelta(days=30)
            
            for row in rows:
                family_id, total, successful, avg_quality, avg_relevance, level, timestamp = row
                
                # Get or create family data
                if family_id not in family_data:
                    family_data[family_id] = {
                        'total_attempts': 0,
                        'successful_attempts': 0,
                        'quality_scores': [],
                        'relevance_scores': [],
                        'levels': set(),
                        'recent_attempts': 0,
                        'recent_successes': 0
                    }
                
                data = family_data[family_id]
                data['total_attempts'] += total
                data['successful_attempts'] += successful
                data['levels'].add(level)
                
                if avg_quality:
                    data['quality_scores'].append(avg_quality)
                if avg_relevance:
                    data['relevance_scores'].append(avg_relevance)
                
                # Recent data for trend analysis
                if timestamp and datetime.fromisoformat(timestamp) >= recent_cutoff:
                    data['recent_attempts'] += total
                    data['recent_successes'] += successful
            
            # Convert to AttackFamilyStats objects
            stats = []
            for family_id, data in family_data.items():
                success_rate = data['successful_attempts'] / data['total_attempts'] if data['total_attempts'] > 0 else 0
                recent_success_rate = data['recent_successes'] / data['recent_attempts'] if data['recent_attempts'] > 0 else 0
                
                # Determine trend
                if recent_success_rate > success_rate * 1.1:
                    trend = "improving"
                elif recent_success_rate < success_rate * 0.9:
                    trend = "declining"
                else:
                    trend = "stable"
                
                stats.append(AttackFamilyStats(
                    family_id=family_id,
                    total_attempts=data['total_attempts'],
                    successful_attempts=data['successful_attempts'],
                    success_rate=success_rate,
                    avg_template_quality=statistics.mean(data['quality_scores']) if data['quality_scores'] else 0,
                    avg_relevance_score=statistics.mean(data['relevance_scores']) if data['relevance_scores'] else 0,
                    levels_used=sorted(list(data['levels'])),
                    recent_success_rate=recent_success_rate,
                    trend=trend
                ))
            
            return sorted(stats, key=lambda x: x.success_rate, reverse=True)
    
    async def get_template_effectiveness(
        self,
        family_filter: Optional[str] = None,
        level_filter: Optional[int] = None
    ) -> List[TemplateStats]:
        """Get effectiveness statistics for templates"""
        
        with self._get_connection() as conn:
            query = """
                SELECT 
                    a.template_id,
                    t.family_id,
                    COUNT(*) as total_uses,
                    SUM(CASE WHEN a.success = 1 THEN 1 ELSE 0 END) as successful_uses,
                    AVG(t.template_quality_score) as avg_quality,
                    AVG(t.template_relevance_score) as avg_relevance,
                    s.level,
                    MAX(t.timestamp) as last_used
                FROM attempts a
                JOIN telemetry t ON a.session_id = t.session_id AND a.attempt_number = t.attempt_number
                JOIN sessions s ON a.session_id = s.id
                WHERE a.template_id IS NOT NULL AND t.family_id IS NOT NULL
            """
            
            params = []
            if family_filter:
                query += " AND t.family_id = ?"
                params.append(family_filter)
            
            if level_filter:
                query += " AND s.level = ?"
                params.append(level_filter)
            
            query += " GROUP BY a.template_id, t.family_id, s.level ORDER BY a.template_id"
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            # Aggregate by template
            template_data: DefaultDict[str, Dict[str, Any]] = defaultdict(lambda: {
                'family_id': None,
                'total_uses': 0,
                'successful_uses': 0,
                'quality_scores': [],
                'relevance_scores': [],
                'levels': set(),
                'last_used': None
            })
            
            for row in rows:
                template_id, family_id, total, successful, avg_quality, avg_relevance, level, last_used = row
                
                # Get or create template data
                if template_id not in template_data:
                    template_data[template_id] = {
                        'family_id': None,
                        'total_uses': 0,
                        'successful_uses': 0,
                        'quality_scores': [],
                        'relevance_scores': [],
                        'levels': set(),
                        'last_used': None
                    }
                
                data = template_data[template_id]
                data['family_id'] = family_id
                data['total_uses'] += total
                data['successful_uses'] += successful
                data['levels'].add(level)
                
                if avg_quality:
                    data['quality_scores'].append(avg_quality)
                if avg_relevance:
                    data['relevance_scores'].append(avg_relevance)
                
                if last_used:
                    current_last = data['last_used']
                    if not current_last or last_used > current_last:
                        data['last_used'] = last_used
            
            # Convert to TemplateStats objects
            stats = []
            for template_id, data in template_data.items():
                success_rate = data['successful_uses'] / data['total_uses'] if data['total_uses'] > 0 else 0
                
                # Simple trend analysis based on recent usage
                trend = "stable"  # Could be enhanced with time-series analysis
                
                stats.append(TemplateStats(
                    template_id=template_id,
                    attack_family=data['family_id'] or "unknown",
                    total_uses=data['total_uses'],
                    successful_uses=data['successful_uses'],
                    success_rate=success_rate,
                    avg_quality_score=statistics.mean(data['quality_scores']) if data['quality_scores'] else 0,
                    avg_relevance_score=statistics.mean(data['relevance_scores']) if data['relevance_scores'] else 0,
                    levels_effective=sorted(list(data['levels'])),
                    last_used=datetime.fromisoformat(data['last_used']) if data['last_used'] else datetime.min,
                    effectiveness_trend=trend
                ))
            
            return sorted(stats, key=lambda x: x.success_rate, reverse=True)
    
    async def get_level_analysis(self) -> List[LevelAnalysis]:
        """Get comprehensive analysis for each Gandalf level"""
        
        with self._get_connection() as conn:
            # Get basic level stats
            cursor = conn.execute("""
                SELECT 
                    s.level,
                    COUNT(DISTINCT s.id) as total_sessions,
                    SUM(CASE WHEN s.status = 'success' THEN 1 ELSE 0 END) as successful_sessions,
                    AVG(CASE WHEN s.status = 'success' THEN 
                        (SELECT COUNT(*) FROM attempts WHERE session_id = s.id) 
                        ELSE NULL END) as avg_attempts_to_success,
                    AVG(CASE WHEN s.completed_at IS NOT NULL AND s.created_at IS NOT NULL THEN
                        (julianday(s.completed_at) - julianday(s.created_at)) * 24 * 60
                        ELSE NULL END) as avg_duration_minutes
                FROM sessions s
                GROUP BY s.level
                ORDER BY s.level
            """)
            
            level_stats = cursor.fetchall()
            
            analyses = []
            for level, total_sessions, successful_sessions, avg_attempts, avg_duration in level_stats:
                success_rate = successful_sessions / total_sessions if total_sessions > 0 else 0
                
                # Get most effective families for this level
                cursor = conn.execute("""
                    SELECT 
                        t.family_id,
                        COUNT(*) as attempts,
                        SUM(CASE WHEN a.success = 1 THEN 1 ELSE 0 END) as successes,
                        CAST(SUM(CASE WHEN a.success = 1 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) as success_rate
                    FROM telemetry t
                    JOIN attempts a ON t.session_id = a.session_id AND t.attempt_number = a.attempt_number
                    JOIN sessions s ON t.session_id = s.id
                    WHERE s.level = ? AND t.family_id IS NOT NULL
                    GROUP BY t.family_id
                    HAVING COUNT(*) >= 3
                    ORDER BY success_rate DESC, attempts DESC
                    LIMIT 5
                """, (level,))
                
                effective_families = [(row[0], row[3]) for row in cursor.fetchall()]
                
                # Get most effective templates for this level
                cursor = conn.execute("""
                    SELECT 
                        a.template_id,
                        COUNT(*) as uses,
                        SUM(CASE WHEN a.success = 1 THEN 1 ELSE 0 END) as successes,
                        CAST(SUM(CASE WHEN a.success = 1 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) as success_rate
                    FROM attempts a
                    JOIN sessions s ON a.session_id = s.id
                    WHERE s.level = ? AND a.template_id IS NOT NULL
                    GROUP BY a.template_id
                    HAVING COUNT(*) >= 2
                    ORDER BY success_rate DESC, uses DESC
                    LIMIT 5
                """, (level,))
                
                effective_templates = [(row[0], row[3]) for row in cursor.fetchall()]
                
                # Analyze failure patterns (simple keyword analysis)
                cursor = conn.execute("""
                    SELECT a.response
                    FROM attempts a
                    JOIN sessions s ON a.session_id = s.id
                    WHERE s.level = ? AND a.success = 0
                    LIMIT 100
                """, (level,))
                
                failure_responses = [row[0] for row in cursor.fetchall()]
                failure_patterns = self._extract_failure_patterns(failure_responses)
                
                analyses.append(LevelAnalysis(
                    level=level,
                    total_sessions=total_sessions,
                    successful_sessions=successful_sessions,
                    success_rate=success_rate,
                    avg_attempts_to_success=avg_attempts or 0,
                    most_effective_families=effective_families,
                    most_effective_templates=effective_templates,
                    common_failure_patterns=failure_patterns,
                    avg_session_duration=avg_duration or 0
                ))
            
            return analyses
    
    def _extract_failure_patterns(self, responses: List[str]) -> List[str]:
        """Extract common patterns from failure responses"""
        if not responses:
            return []
        
        # Common failure indicators
        patterns = {
            "refusal": r"(?i)(cannot|can't|won't|refuse|not allowed|not permitted)",
            "deflection": r"(?i)(nice try|clever|interesting|good attempt)",
            "confusion": r"(?i)(don't understand|unclear|confusing|what do you mean)",
            "security": r"(?i)(security|protect|guard|safe|secure)",
            "policy": r"(?i)(policy|rules|guidelines|instructions)",
            "redirect": r"(?i)(instead|however|but|although|different topic)"
        }
        
        pattern_counts = Counter()
        for response in responses:
            if response:
                for pattern_name, pattern_regex in patterns.items():
                    if re.search(pattern_regex, response):
                        pattern_counts[pattern_name] += 1
        
        # Return top patterns with counts
        return [f"{pattern} ({count} occurrences)" 
                for pattern, count in pattern_counts.most_common(5)]
    
    async def identify_session_patterns(self, limit: int = 50) -> List[SessionPattern]:
        """Identify patterns in session progression"""
        
        with self._get_connection() as conn:
            # Get recent sessions with their attempt sequences
            cursor = conn.execute("""
                SELECT 
                    s.id,
                    s.status,
                    GROUP_CONCAT(a.success, ',') as success_sequence,
                    GROUP_CONCAT(t.family_id, ',') as family_sequence
                FROM sessions s
                LEFT JOIN attempts a ON s.id = a.session_id
                LEFT JOIN telemetry t ON s.id = t.session_id AND a.attempt_number = t.attempt_number
                WHERE s.created_at >= datetime('now', '-30 days')
                GROUP BY s.id
                ORDER BY s.created_at DESC
                LIMIT ?
            """, (limit,))
            
            sessions = cursor.fetchall()
            
            patterns = []
            
            # Analyze success sequences
            success_sequences = []
            breakthrough_sessions = []
            
            for session_id, status, success_seq, family_seq in sessions:
                if success_seq:
                    seq = [int(x) for x in success_seq.split(',') if x.strip()]
                    success_sequences.append((session_id, seq, status))
                    
                    # Look for breakthrough patterns (long failure followed by success)
                    if len(seq) > 5 and seq[-1] == 1 and sum(seq[-6:-1]) == 0:
                        breakthrough_sessions.append(session_id)
            
            # Common success sequence patterns
            if success_sequences:
                # Quick success pattern (success in first 3 attempts)
                quick_successes = [s for s in success_sequences if len(s[1]) <= 3 and s[2] == 'success']
                if quick_successes:
                    patterns.append(SessionPattern(
                        pattern_type="quick_success",
                        description="Sessions that succeed within first 3 attempts",
                        frequency=len(quick_successes),
                        success_correlation=1.0,
                        example_sessions=[s[0] for s in quick_successes[:3]]
                    ))
                
                # Breakthrough pattern
                if breakthrough_sessions:
                    patterns.append(SessionPattern(
                        pattern_type="breakthrough",
                        description="Sessions with breakthrough after extended failure",
                        frequency=len(breakthrough_sessions),
                        success_correlation=1.0,
                        example_sessions=breakthrough_sessions[:3]
                    ))
            
            return patterns
    
    async def get_telemetry_summary(self) -> Dict[str, Any]:
        """Get high-level telemetry summary"""
        
        with self._get_connection() as conn:
            # Overall stats
            cursor = conn.execute("""
                SELECT 
                    COUNT(DISTINCT s.id) as total_sessions,
                    COUNT(DISTINCT t.session_id) as sessions_with_telemetry,
                    COUNT(*) as total_telemetry_records,
                    AVG(t.template_success_rate) as avg_template_success_rate,
                    AVG(t.family_success_rate) as avg_family_success_rate,
                    AVG(t.coverage_percentage) as avg_coverage,
                    COUNT(DISTINCT t.family_id) as unique_families,
                    COUNT(DISTINCT a.template_id) as unique_templates
                FROM sessions s
                LEFT JOIN telemetry t ON s.id = t.session_id
                LEFT JOIN attempts a ON s.id = a.session_id AND t.attempt_number = a.attempt_number
                WHERE t.id IS NOT NULL
            """)
            
            stats = cursor.fetchone()
            
            # Recent activity (last 7 days)
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT t.session_id) as recent_sessions
                FROM telemetry t
                WHERE t.timestamp >= datetime('now', '-7 days')
            """)
            
            recent_sessions = cursor.fetchone()[0]
            
            # Top performing families
            cursor = conn.execute("""
                SELECT 
                    t.family_id,
                    COUNT(*) as attempts,
                    SUM(CASE WHEN a.success = 1 THEN 1 ELSE 0 END) as successes,
                    CAST(SUM(CASE WHEN a.success = 1 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) as success_rate
                FROM telemetry t
                JOIN attempts a ON t.session_id = a.session_id AND t.attempt_number = a.attempt_number
                WHERE t.family_id IS NOT NULL
                GROUP BY t.family_id
                HAVING COUNT(*) >= 5
                ORDER BY success_rate DESC
                LIMIT 5
            """)
            
            top_families = [{"family": row[0], "success_rate": row[3], "attempts": row[1]} 
                           for row in cursor.fetchall()]
            
            return {
                "overview": {
                    "total_sessions": stats[0] or 0,
                    "sessions_with_telemetry": stats[1] or 0,
                    "total_telemetry_records": stats[2] or 0,
                    "recent_sessions_7d": recent_sessions or 0
                },
                "averages": {
                    "template_success_rate": round(stats[3] or 0, 3),
                    "family_success_rate": round(stats[4] or 0, 3),
                    "coverage_percentage": round(stats[5] or 0, 1)
                },
                "diversity": {
                    "unique_attack_families": stats[6] or 0,
                    "unique_templates": stats[7] or 0
                },
                "top_performing_families": top_families
            }
    
    async def export_telemetry_data(
        self,
        format: str = "json",
        level_filter: Optional[int] = None,
        days_back: Optional[int] = None
    ) -> Dict[str, Any]:
        """Export telemetry data for external analysis"""
        
        with self._get_connection() as conn:
            query = """
                SELECT 
                    s.id as session_id,
                    s.level,
                    s.status as session_status,
                    s.created_at,
                    s.completed_at,
                    a.attempt_number,
                    a.prompt,
                    a.response,
                    a.success,
                    a.attack_family,
                    a.template_id,
                    t.template_success_rate,
                    t.template_quality_score,
                    t.template_relevance_score,
                    t.family_success_rate,
                    t.family_selection_probability,
                    t.coverage_percentage,
                    t.raw_telemetry
                FROM sessions s
                JOIN attempts a ON s.id = a.session_id
                LEFT JOIN telemetry t ON s.id = t.session_id AND a.attempt_number = t.attempt_number
                WHERE 1=1
            """
            
            params = []
            if level_filter:
                query += " AND s.level = ?"
                params.append(level_filter)
            
            if days_back:
                query += " AND s.created_at >= ?"
                params.append(datetime.now() - timedelta(days=days_back))
            
            query += " ORDER BY s.created_at DESC, a.attempt_number"
            
            cursor = conn.execute(query, params)
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            data = []
            for row in rows:
                record = dict(zip(columns, row))
                # Parse raw telemetry if present
                if record['raw_telemetry']:
                    try:
                        record['raw_telemetry'] = json.loads(record['raw_telemetry'])
                    except json.JSONDecodeError:
                        record['raw_telemetry'] = None
                data.append(record)
            
            return {
                "export_timestamp": datetime.now().isoformat(),
                "total_records": len(data),
                "filters": {
                    "level": level_filter,
                    "days_back": days_back
                },
                "data": data
            }
