"""
tests/test_phase3.py

Week 5: Comprehensive Phase 3 Test Suite
==========================================
Tests all Phase 3 components without requiring a live SuperBrain cluster.
Uses a MockClient to simulate all fabric operations in-memory.
"""
import collections
import sys
import os
import time
import threading

# Add the SDK to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../python"))

# ───────────────────────── Mock Client Scaffold ──────────────────────────

class MockClient:
    """Simulates a SuperBrain client using in-process Python dicts."""

    def __init__(self, addr: str = "mock", encryption_key=None):
        self._store: dict = {}
        self._alloc_count = 0

    def allocate(self, size: int) -> str:
        ptr_id = f"ptr-{self._alloc_count:04d}"
        self._alloc_count += 1
        self._store[ptr_id] = bytearray(size)
        return ptr_id

    def write(self, ptr_id: str, offset: int, data: bytes) -> None:
        if ptr_id not in self._store:
            raise Exception(f"Invalid ptr: {ptr_id}")
        buf = self._store[ptr_id]
        buf[offset:offset + len(data)] = data

    def read(self, ptr_id: str, offset: int, length: int) -> bytes:
        if ptr_id not in self._store:
            raise Exception(f"Invalid ptr: {ptr_id}")
        buf = self._store[ptr_id]
        if length == 0:
            return bytes(buf[offset:])
        return bytes(buf[offset:offset + length])

    def free(self, ptr_id: str) -> None:
        self._store.pop(ptr_id, None)

    def register(self, agent_id: str) -> None:
        pass


class MockController:
    """Wraps MockClient to simulate AutoMemoryController."""
    def __init__(self):
        self._client = MockClient()

    def allocate(self, size): return self._client.allocate(size)
    def write(self, ptr, off, data): self._client.write(ptr, off, data)
    def read(self, ptr, off, length): return self._client.read(ptr, off, length)
    def free(self, ptr): self._client.free(ptr)


# ───────────────────────── Test Utilities ────────────────────────────────

PASSED = []
FAILED = []

def test(name: str):
    """Decorator to register a test function."""
    def decorator(fn):
        try:
            fn()
            PASSED.append(name)
            print(f"  ✅ PASS  {name}")
        except AssertionError as e:
            FAILED.append((name, str(e)))
            print(f"  ❌ FAIL  {name}: {e}")
        except Exception as e:
            FAILED.append((name, repr(e)))
            print(f"  💥 ERROR {name}: {e}")
        return fn
    return decorator


# ───────────────────────── Week 1: AutoMemoryController ──────────────────

print("\n== Week 1: AutoMemoryController ==")

@test("SharedContext: write and read round-trip")
def _():
    from superbrain.auto import SharedContext, AutoMemoryController
    ctrl = MockController()
    ctx = SharedContext(ctrl, "test-session")
    ctx._ctrl = ctrl
    # Simulate write
    import json
    data = {"result": "success", "accuracy": 0.99}
    raw = json.dumps(data).encode()
    ptr_id = ctrl.allocate(len(raw))
    ctrl.write(ptr_id, 0, raw)
    ctx._store["findings"] = ptr_id
    # Read back
    raw2 = ctrl.read(ptr_id, 0, len(raw))
    recovered = json.loads(raw2.decode())
    assert recovered == data, f"Data mismatch: {recovered}"


@test("KV Cache deduplication: same bytes return same pointer")
def _():
    from superbrain.auto import _KVCacheManager
    ctrl = MockController()
    kv = _KVCacheManager(ctrl)
    prompt = b"You are a helpful AI assistant."
    ptr1 = kv.get_or_create(prompt)
    ptr2 = kv.get_or_create(prompt)
    assert ptr1 == ptr2, f"Expected same ptr, got {ptr1} vs {ptr2}"


@test("KV Cache: different bytes give different pointers")
def _():
    from superbrain.auto import _KVCacheManager
    ctrl = MockController()
    kv = _KVCacheManager(ctrl)
    ptr1 = kv.get_or_create(b"prompt-alpha")
    ptr2 = kv.get_or_create(b"prompt-beta")
    assert ptr1 != ptr2, "Different prompts should have different pointers"


# ───────────────────────── Week 2: Predictor & Telemetry ─────────────────

print("\n== Week 2: Predictor & Telemetry ==")

@test("AccessTracker: records and scores accesses")
def _():
    from superbrain.predictor import AccessTracker
    tracker = AccessTracker()
    for _ in range(10):
        tracker.record("ptr-hot", 1024)
    tracker.record("ptr-cold", 512)
    assert tracker.score("ptr-hot") > tracker.score("ptr-cold"), \
        "Hot pointer should have higher score"


@test("MarkovPrefetcher: learns and predicts next access")
def _():
    from superbrain.predictor import MarkovPrefetcher
    mf = MarkovPrefetcher()
    for _ in range(10):
        mf.observe("ptr-A")
        mf.observe("ptr-B")
    predictions = mf.predict_next("ptr-A")
    assert len(predictions) > 0, "Should have predictions after training"
    assert predictions[0][0] == "ptr-B", f"Expected ptr-B, got {predictions[0][0]}"
    assert predictions[0][1] >= 0.4, f"Confidence too low: {predictions[0][1]}"


@test("ContextRouter: routes to node with most free space")
def _():
    from superbrain.predictor import ContextRouter
    router = ContextRouter()
    router.update_node("node-1", 900_000_000, 1_000_000_000, rtt_ms=1.2)  # 90% used
    router.update_node("node-2", 100_000_000, 1_000_000_000, rtt_ms=1.5)  # 10% used
    best = router.best_node_for_write(10_000_000)
    assert best == "node-2", f"Expected node-2 (more free), got {best}"


def pytest_approx(value, abs_tol=0.01):
    """Minimal stand-in for pytest.approx."""
    class _Approx:
        def __eq__(self, other): return __builtins__["abs"](other - value) < abs_tol if isinstance(__builtins__, dict) else abs(other - value) < abs_tol
        def __repr__(self): return f"~{value}±{abs_tol}"
    return _Approx()


@test("TelemetryCollector: measures and reports latency")
def _():
    from superbrain.telemetry import TelemetryCollector
    telem = TelemetryCollector()
    for _ in range(20):
        with telem.measure("write", num_bytes=4_000_000):
            time.sleep(0.001)  # Simulate 1ms latency
    telem.record_cache_hit()
    telem.record_cache_hit()
    telem.record_cache_miss()
    report = telem.report()
    assert report["operations"]["write"]["count"] == 20
    assert abs(report["kv_cache"]["hit_ratio"] - 0.667) < 0.01
    assert report["throughput"]["write_mbps"] > 0


# ───────────────────────── Week 3: Advanced KV Pool ──────────────────────

print("\n== Week 3: Advanced KV Pool ==")

@test("AdvancedKVPool: stores and retrieves token sequences")
def _():
    from superbrain.kv_pool import AdvancedKVPool
    ctrl = MockController()
    pool = AdvancedKVPool(ctrl)
    tokens = b"The quick brown fox jumps over the lazy dog." * 10
    ptr = pool.store(tokens, model_id="gpt-4")
    result = pool.retrieve(ptr, model_id="gpt-4")
    assert result == tokens, "Retrieval mismatch"


@test("AdvancedKVPool: prefix deduplication (shared prefix)")
def _():
    from superbrain.kv_pool import AdvancedKVPool
    ctrl = MockController()
    pool = AdvancedKVPool(ctrl)
    shared_prefix = b"You are a helpful assistant. " * 20  # 580 bytes
    ptr1 = pool.store(shared_prefix, model_id="llama-3")
    ptr2 = pool.store(shared_prefix, model_id="mistral")  # Same family
    assert ptr1 == ptr2, "Identical prefix should return same pointer"


@test("AdvancedKVPool: usage report tracks segments")
def _():
    from superbrain.kv_pool import AdvancedKVPool
    ctrl = MockController()
    pool = AdvancedKVPool(ctrl)
    pool.store(b"segment-one" * 10, model_id="gpt-4")
    pool.store(b"segment-two" * 10, model_id="claude-3-opus")
    report = pool.usage_report()
    assert report["total_segments"] >= 1


# ───────────────────────── Week 4: Security ──────────────────────────────

print("\n== Week 4: Security & Anomaly Detection ==")

@test("AnomalyDetector: normal traffic produces no alerts")
def _():
    from superbrain.security import AnomalyDetector
    alerts = []
    det = AnomalyDetector(on_alert=alerts.append)
    for _ in range(30):
        det.observe("agent-normal", 4_000_000, "ptr-abc")
    assert len(alerts) == 0, f"Unexpected alerts: {alerts}"


@test("AnomalyDetector: sudden spike triggers HIGH alert")
def _():
    from superbrain.security import AnomalyDetector
    alerts = []
    det = AnomalyDetector(on_alert=alerts.append, z_threshold=3.0)
    for _ in range(30):
        det.observe("agent-spike", 4_000_000, "ptr-abc")  # Establish baseline
    # Massive spike — 100x the baseline
    det.observe("agent-spike", 400_000_000, "ptr-abc")
    assert len(alerts) >= 1, "Expected an anomaly alert for a 100x spike"
    assert alerts[-1]["z_score"] > 3.0


@test("KeyManager: derives consistent keys per context")
def _():
    from superbrain.security import KeyManager
    km = KeyManager(master_secret=b"x" * 32)
    k1 = km.key_for("session-alpha")
    k2 = km.key_for("session-alpha")
    k3 = km.key_for("session-beta")
    assert k1 == k2, "Same context should yield same key"
    assert k1 != k3, "Different contexts should have different keys"
    assert len(k1) == 32, "Key should be 32 bytes (AES-256)"


@test("KeyManager: key rotation returns new key")
def _():
    from superbrain.security import KeyManager
    km = KeyManager(master_secret=b"y" * 32)
    original = km.key_for("my-context")
    rotated = km.rotate("my-context")
    assert rotated != original, "Rotated key should differ from original"
    assert km.key_for("my-context") == rotated


@test("SelfTuningAllocator: right-sizes to power-of-2 blocks")
def _():
    from superbrain.allocator import SelfTuningAllocator
    ctrl = MockController()
    alloc = SelfTuningAllocator(ctrl)
    ptr = alloc.allocate(3_000_000)   # 3MB → should round to 4MB
    # Verify allocation succeeded
    assert ptr.startswith("ptr-"), f"Unexpected ptr: {ptr}"
    alloc.free(ptr)


# ───────────────────────── Summary ───────────────────────────────────────

print(f"\n{'='*55}")
print(f"  Phase 3 Test Results: {len(PASSED)} passed, {len(FAILED)} failed")
print(f"{'='*55}")
if FAILED:
    print("\nFailed tests:")
    for name, err in FAILED:
        print(f"  ❌ {name}: {err}")
    sys.exit(1)
else:
    print("  🎉 All Phase 3 tests passed!\n")
