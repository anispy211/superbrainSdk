# 🧠 superbrain-distributed-sdk v0.2.0 — TypeScript/Node.js

[![npm version](https://badge.fury.io/js/superbrain-distributed-sdk.svg)](https://badge.fury.io/js/superbrain-distributed-sdk)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Node.js](https://img.shields.io/badge/Node.js-18%2B-green)](https://nodejs.org)

> **The Distributed RAM Fabric for AI Agents** — Share terabytes of context across your LLM cluster at microsecond speeds using 36-byte UUID pointers.

---

## 📦 Installation

```bash
npm install superbrain-distributed-sdk
```

---

## ✨ New in v0.2.0 — Phase 3: Automated AI Memory Controller

Version 0.2.0 introduces the Phase 3 **Automated AI Memory Controller** — a self-managing, intelligent memory fabric where multiple LLMs running on different machines share context instantly at RAM speed.

### Key Phase 3 Features:
- **Auto-Discovery**: Zero-config cluster formation via mDNS
- **KV Cache Pooling**: Identical prefixes shared across models automatically
- **Smart Prefetching**: Markov-chain access pattern prediction
- **Self-Tuning Allocator**: Learns from access history to pre-allocate
- **Anomaly Detection**: Z-score alerting for unusual access patterns
- **Live Dashboard**: Real-time metrics at `http://localhost:9090`

---

## 🔧 Usage

### Basic — Shared Memory Between Agents
```typescript
import { SuperbrainClient } from 'superbrain-distributed-sdk';

const client = new SuperbrainClient('localhost:50050');
await client.register('my-agent-id');

// Allocate distributed RAM
const ptrId = await client.allocate(100 * 1024 * 1024); // 100 MB

// Write from Agent A on Machine A
await client.write(ptrId, 0, Buffer.from('Shared AI context'));

// Read from Agent B on Machine B (just needs the 36-byte pointer!)
const data = await client.read(ptrId, 0, 17);

await client.free(ptrId);
client.close();
```

### Advanced — Secure Fabric (E2EE)
```typescript
import { SuperbrainClient } from 'superbrain-distributed-sdk';

// All data encrypted with AES-256-GCM at client level
// Memory nodes NEVER see plaintext
const client = new SuperbrainClient('localhost:50050', {
  encryptionKey: crypto.randomBytes(32)
});
await client.register('secure-agent');

const ptr = await client.allocate(4 * 1024 * 1024);
await client.write(ptr, 0, Buffer.from(JSON.stringify(sensitiveData)));
const response = await client.read(ptr, 0, 0);
```

### Multi-Agent Context Passing
```typescript
// Agent A writes — gets pointer
const ctxPtr = await client.allocate(1024 * 1024);
await client.write(ctxPtr, 0, Buffer.from(JSON.stringify({
  topic: "distributed AI inference",
  findings: researchResults,
  timestamp: Date.now()
})));

// Share the 36-byte pointer ID via any channel (HTTP, gRPC, etc.)
broadcast({ contextPtr: ctxPtr }); // other agents connect immediately

// Agent B reads — microseconds, no data copying
const received = JSON.parse((await clientB.read(ctxPtr, 0, 0)).toString());
```

---

## 📊 Architecture

```
Your LLM App             SuperBrain Cluster
┌──────────────┐         ┌──────────────────────┐
│ Node.js SDK  │──gRPC──>│   Coordinator        │
│              │         │   (Control Plane)     │
│  allocate()  │         └──────────┬───────────┘
│  write()     │                    │ pointer map
│  read()      │         ┌──────────▼───────────┐
│  free()      │──gRPC──>│   Memory Nodes        │
└──────────────┘         │   (Data Plane)        │
                         │   1TB+ pooled RAM     │
                         └──────────────────────┘
```

**Control plane** (Coordinator): Routes allocation requests, maintains node registry.  
**Data plane** (Memory Nodes): Direct gRPC streams for maximum throughput.  
**Client**: Talks to nodes directly after allocation — Coordinator is never in the hot path.

---

## 🔐 Security Features

| Feature | Status |
|---------|--------|
| mTLS (mutual TLS between all nodes) | ✅ |
| E2EE (AES-256-GCM at SDK level) | ✅ |
| Pub/Sub (real-time memory notifications) | ✅ |
| Per-context key rotation | ✅ (v0.2.0) |
| Anomaly detection | ✅ (v0.2.0) |
| GDPR/SOC2 audit logging | ✅ (v0.2.0) |

---

## 🗺️ Roadmap

| Version | Milestone | Status |
|---------|-----------|--------|
| `v0.1.0` | Core Distributed RAM | ✅ Shipped |
| `v0.1.1` | Secure Fabric (mTLS + E2EE) | ✅ Shipped |
| `v0.2.0` | **Phase 3: Automated AI Memory Controller** | ✅ **Current** |
| `v0.3.0` | Raft Replication (Fault-Tolerant Memory) | 🚧 Planned |
| `v0.4.0` | NVMe Spilling ("Infinite Memory") | 🚧 Planned |
| `v0.5.0` | GPUDirect RDMA (GPU→Network zero-copy) | 🔬 Research |

---

## 📚 Documentation

- [Full Documentation & API Reference](https://github.com/anispy211/superbrainSdk/blob/main/DOCUMENTATION.md)
- [GitHub Repository](https://github.com/anispy211/superbrainSdk)
- [Main Server Repo](https://github.com/anispy211/memorypool)

---

## 🖥️ Server Setup (Required)

This SDK connects to a **SuperBrain coordinator**. To run one locally in 30 seconds:

```bash
git clone https://github.com/anispy211/memorypool
cd memorypool
docker compose up -d
# Dashboard: http://localhost:8080
```

---

MIT License · Built by [Anispy](https://github.com/anispy211)
