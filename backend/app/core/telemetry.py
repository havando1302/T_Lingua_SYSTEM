"""
Pipeline Telemetry and Metrics Tracker (Phase 5 Performance Optimization)
Gắn số đo vào toàn pipeline: thời điểm nhận lượt, vào/ra queue, xử lý STT/dịch/TTS.
Cung cấp thống kê P50, P90, P99 và throughput không gây nghẽn event loop.
"""
import time
import statistics
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import threading
from datetime import datetime, timezone, timedelta

@dataclass
class TurnMetric:
    turn_id: str
    session_id: str
    t_turn_received: float = field(default_factory=time.perf_counter)
    t_queue_in: Optional[float] = None
    t_queue_out: Optional[float] = None
    t_stt_start: Optional[float] = None
    t_stt_done: Optional[float] = None
    t_translate_start: Optional[float] = None
    t_translate_done: Optional[float] = None
    t_tts_start: Optional[float] = None
    t_tts_chunk_0: Optional[float] = None
    t_tts_done: Optional[float] = None
    audio_duration_s: float = 0.0
    text_length: int = 0
    error: Optional[str] = None
    source_lang: str = "vi"
    target_lang: str = "en"

    @property
    def queue_wait_ms(self) -> float:
        if self.t_queue_in and self.t_queue_out:
            return max(0.0, (self.t_queue_out - self.t_queue_in) * 1000)
        return 0.0

    @property
    def stt_ms(self) -> float:
        if self.t_stt_start and self.t_stt_done:
            return max(0.0, (self.t_stt_done - self.t_stt_start) * 1000)
        return 0.0

    @property
    def translate_ms(self) -> float:
        if self.t_translate_start and self.t_translate_done:
            return max(0.0, (self.t_translate_done - self.t_translate_start) * 1000)
        return 0.0

    @property
    def tts_first_chunk_ms(self) -> float:
        if self.t_tts_start and self.t_tts_chunk_0:
            return max(0.0, (self.t_tts_chunk_0 - self.t_tts_start) * 1000)
        return 0.0

    @property
    def tts_total_ms(self) -> float:
        if self.t_tts_start and self.t_tts_done:
            return max(0.0, (self.t_tts_done - self.t_tts_start) * 1000)
        return 0.0

    @property
    def total_latency_ms(self) -> float:
        end_time = self.t_tts_done or self.t_translate_done or self.t_stt_done
        if end_time:
            return max(0.0, (end_time - self.t_turn_received) * 1000)
        return 0.0


class PipelineTelemetryTracker:
    def __init__(self, max_history: int = 1000):
        self._max_history = max_history
        self._lock = threading.Lock()
        self._active_metrics: Dict[str, TurnMetric] = {}
        self._completed_metrics: deque[TurnMetric] = deque(maxlen=max_history)
        self._total_turns_processed: int = 0
        self._total_errors: int = 0
        self._start_time: float = time.time()
        self._daily: dict = {}
        self._language_counts: dict = {}
        self._total_cancelled = 0

    def start_turn(self, turn_id: str, session_id: str, audio_duration_s: float = 0.0,
                   source_lang: str = "vi", target_lang: str = "en") -> TurnMetric:
        with self._lock:
            if turn_id in self._active_metrics:
                return self._active_metrics[turn_id]
            # Active work is bounded too, including a caller that disconnects mid-inference.
            if len(self._active_metrics) >= self._max_history:
                self._active_metrics.pop(next(iter(self._active_metrics)))
            metric = TurnMetric(
                turn_id=turn_id,
                session_id=session_id,
                audio_duration_s=audio_duration_s,
                t_turn_received=time.perf_counter(),
                source_lang={"vie_Latn": "vi", "eng_Latn": "en"}.get(source_lang, source_lang),
                target_lang={"vie_Latn": "vi", "eng_Latn": "en"}.get(target_lang, target_lang),
            )
            self._active_metrics[turn_id] = metric
            return metric

    def get_turn(self, turn_id: str) -> Optional[TurnMetric]:
        with self._lock:
            return self._active_metrics.get(turn_id)

    def record_stage(self, turn_id: str, stage: str, **kwargs) -> None:
        with self._lock:
            metric = self._active_metrics.get(turn_id)
            if not metric:
                return
            now = time.perf_counter()
            if stage == "queue_in":
                metric.t_queue_in = now
            elif stage == "queue_out":
                metric.t_queue_out = now
            elif stage == "stt_start":
                metric.t_stt_start = now
            elif stage == "stt_done":
                metric.t_stt_done = now
            elif stage == "translate_start":
                metric.t_translate_start = now
            elif stage == "translate_done":
                metric.t_translate_done = now
            elif stage == "tts_start":
                metric.t_tts_start = now
            elif stage == "tts_chunk_0":
                if metric.t_tts_chunk_0 is None:
                    metric.t_tts_chunk_0 = now
            elif stage == "tts_done":
                metric.t_tts_done = now
            elif stage == "error":
                if metric.error is None:
                    self._total_errors += 1
                metric.error = kwargs.get("error", "Unknown error")

    def complete_turn(self, turn_id: str) -> Optional[TurnMetric]:
        with self._lock:
            metric = self._active_metrics.pop(turn_id, None)
            if metric:
                self._completed_metrics.append(metric)
                self._total_turns_processed += 1
                day = datetime.now(timezone.utc).date().isoformat()
                daily = self._daily.setdefault(day, {"requests": 0, "total_latency_ms": 0.0})
                daily["requests"] += 1
                daily["total_latency_ms"] += metric.total_latency_ms
                oldest = (datetime.now(timezone.utc).date() - timedelta(days=6)).isoformat()
                self._daily = {d: values for d, values in self._daily.items() if d >= oldest}
                pair = (metric.source_lang, metric.target_lang)
                self._language_counts[pair] = self._language_counts.get(pair, 0) + 1
            return metric

    def discard_turn(self, turn_id: str, *, error: str | None = None) -> None:
        with self._lock:
            metric = self._active_metrics.pop(turn_id, None)
            if metric:
                if error and metric.error is None:
                    self._total_errors += 1
                elif not error:
                    self._total_cancelled += 1

    def get_activity_summary(self) -> dict:
        """Content-free process metrics; never persist transcript or translation text."""
        with self._lock:
            samples = list(self._completed_metrics)
            return {
                "scope": "since_process_start", "started_at": datetime.fromtimestamp(self._start_time, timezone.utc).isoformat(),
                "sample_limit": self._max_history,
                "total_translations": self._total_turns_processed,
                "unique_clients": len({m.session_id for m in samples}),
                "avg_latency": round(statistics.mean([m.total_latency_ms for m in samples]) / 1000, 3) if samples else 0.0,
                "timeseries": [{"date": day, "requests": data["requests"],
                                "avg_latency": round(data["total_latency_ms"] / data["requests"] / 1000, 3)}
                               for day, data in sorted(self._daily.items())],
                "languages": [{"source_lang": pair[0], "target_lang": pair[1], "value": count}
                              for pair, count in sorted(self._language_counts.items())],
            }

    def get_summary(self) -> Dict[str, Any]:
        with self._lock:
            completed = list(self._completed_metrics)
            active_count = len(self._active_metrics)
            uptime_s = max(1.0, time.time() - self._start_time)

        if not completed:
            return {
                "active_turns": active_count,
                "total_completed": self._total_turns_processed,
                "total_errors": self._total_errors,
                "throughput_turns_per_sec": round(self._total_turns_processed / uptime_s, 2),
                "latencies_ms": {
                    "queue_wait": {"p50": 0.0, "p90": 0.0, "p99": 0.0, "avg": 0.0},
                    "stt": {"p50": 0.0, "p90": 0.0, "p99": 0.0, "avg": 0.0},
                    "translate": {"p50": 0.0, "p90": 0.0, "p99": 0.0, "avg": 0.0},
                    "tts_first_chunk": {"p50": 0.0, "p90": 0.0, "p99": 0.0, "avg": 0.0},
                    "tts_total": {"p50": 0.0, "p90": 0.0, "p99": 0.0, "avg": 0.0},
                    "end_to_end": {"p50": 0.0, "p90": 0.0, "p99": 0.0, "avg": 0.0},
                },
            }

        def _calc_percentiles(values: List[float]) -> Dict[str, float]:
            if not values:
                return {"p50": 0.0, "p90": 0.0, "p99": 0.0, "avg": 0.0}
            sorted_vals = sorted(values)
            n = len(sorted_vals)
            p50 = sorted_vals[int(n * 0.50)]
            p90 = sorted_vals[min(int(n * 0.90), n - 1)]
            p99 = sorted_vals[min(int(n * 0.99), n - 1)]
            avg = statistics.mean(sorted_vals)
            return {
                "p50": round(p50, 2),
                "p90": round(p90, 2),
                "p99": round(p99, 2),
                "avg": round(avg, 2),
            }

        queue_waits = [m.queue_wait_ms for m in completed if m.queue_wait_ms > 0]
        stt_times = [m.stt_ms for m in completed if m.stt_ms > 0]
        trans_times = [m.translate_ms for m in completed if m.translate_ms > 0]
        tts_chunk0_times = [m.tts_first_chunk_ms for m in completed if m.tts_first_chunk_ms > 0]
        tts_totals = [m.tts_total_ms for m in completed if m.tts_total_ms > 0]
        e2e_latencies = [m.total_latency_ms for m in completed if m.total_latency_ms > 0]

        return {
            "active_turns": active_count,
            "total_completed": self._total_turns_processed,
            "total_errors": self._total_errors,
            "throughput_turns_per_sec": round(self._total_turns_processed / uptime_s, 2),
            "latencies_ms": {
                "queue_wait": _calc_percentiles(queue_waits),
                "stt": _calc_percentiles(stt_times),
                "translate": _calc_percentiles(trans_times),
                "tts_first_chunk": _calc_percentiles(tts_chunk0_times),
                "tts_total": _calc_percentiles(tts_totals),
                "end_to_end": _calc_percentiles(e2e_latencies),
            },
        }

# Global singleton instance
GLOBAL_TELEMETRY = PipelineTelemetryTracker()
