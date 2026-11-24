# Kajenn SPA capacity on Apple M4

Measured on 24 November 2026 using an Apple M4 with 10 logical cores, 24 GiB RAM and macOS 27.0.1. The synthetic clients and the server shared the host and communicated over loopback. Each configuration ran separately. A single application served two tabs per authenticated user with one user-scoped store and one WebSocket per tab. The default persistent page policy was enabled.

All measurements used the develop builds of Kajenn (`b327070`, 0.10.0), Gramlot (`b505cbaf`, 0.3.40) and gramlot-py-server (`342a612`, 0.3.31). The Python version was 3.12.12. Each invocation started a fresh site. Setup admitted users in batches of eight. Setup and the idle period were excluded from active latency measurements. Both process placements used the same workload and success criteria.

## Highest passing levels

- In process, 5-second interval: 1,000 users, 2,000 sockets and 400 operations/s passed. This was the highest level tested.
- In process, 1-second interval: 500 users, 1,000 sockets and 1,000 operations/s passed. The first failed level was 750 users with binding/RPC p95 of 170.2/312.8 ms and 0 missing operations.
- Separate application process, 5-second interval: 1,000 users, 2,000 sockets and 400 operations/s passed. This was the highest level tested.
- Separate application process, 1-second interval: 750 users, 1,500 sockets and 1,500 operations/s passed. The first failed level was 1,000 users with binding/RPC p95 of 1143.5/4378.7 ms and 0 missing operations.

At 750 users, an independent one-minute run confirmed the distinction. RPC p95 was 323.9 ms in process and 55.1 ms with the separate application. All 90,000 operations arrived in each run. For this workload, use one process at the lighter rate, consider the separate application near 750 continuously active users, and evaluate multiple application workers if roughly 2,000 operations/s are required. Validate that decision with real application requests on the deployment host.

## Measurements

Each user issued one cross-tab binding change and one echo RPC per interval. Operations/s is the offered rate for both streams together. Latency starts at the scheduled arrival and ends at the matching response. The target was zero missing operations, every socket alive, and p95 up to 250 ms for both streams. Each row is one run at that level.

### Standard page limit

1,000 registered pages, four cycles five seconds apart and an eight-second idle window.

| Placement | Users | WS open | Offered ops/s | Bind p95 ms | RPC p95 ms | Missing | Front CPU % | App CPU % | Pass |
|---|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| local | 16 | 32 | 6 | 4.5 | 5.6 | 0 | 1.3 | — | Yes |
| local | 64 | 128 | 26 | 5.2 | 6.1 | 0 | 4.6 | — | Yes |
| local | 128 | 256 | 51 | 5.4 | 6.7 | 0 | 10.1 | — | Yes |
| local | 256 | 512 | 102 | 5.4 | 7.0 | 0 | 18.8 | — | Yes |
| local | 384 | 768 | 154 | 5.0 | 5.9 | 0 | 22.0 | — | Yes |
| local | 500 | 1000 | 200 | 4.3 | 5.3 | 0 | 26.5 | — | Yes |
| subprocess | 16 | 32 | 6 | 5.5 | 6.2 | 0 | 1.0 | 0.9 | Yes |
| subprocess | 64 | 128 | 26 | 6.3 | 7.3 | 0 | 3.4 | 3.7 | Yes |
| subprocess | 128 | 256 | 51 | 6.6 | 7.3 | 0 | 6.4 | 7.5 | Yes |
| subprocess | 256 | 512 | 102 | 5.6 | 6.3 | 0 | 10.1 | 13.3 | Yes |
| subprocess | 384 | 768 | 154 | 5.4 | 6.0 | 0 | 11.0 | 16.5 | Yes |
| subprocess | 500 | 1000 | 200 | 4.8 | 5.3 | 0 | 13.2 | 21.2 | Yes |

Reproduce independently for each placement from the repository root.

```sh
python benchmarks/kajennspa/run.py local --levels 16,64,128,256,384,500 --output local.json
python benchmarks/kajennspa/run.py subprocess --levels 16,64,128,256,384,500 --output subprocess.json
```

Raw measurements include setup p95, idle ping counts, p99, error counts, CPU and sampled peak RSS for each process. [local JSON](results/2026-11-24-local.json), [subprocess JSON](results/2026-11-24-subprocess.json).

### Raised page limit

2,000 registered pages, six cycles five seconds apart and a five-second idle window.

| Placement | Users | WS open | Offered ops/s | Bind p95 ms | RPC p95 ms | Missing | Front CPU % | App CPU % | Pass |
|---|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| local | 500 | 1000 | 200 | 4.7 | 5.6 | 0 | 25.4 | — | Yes |
| local | 750 | 1500 | 300 | 3.9 | 4.4 | 0 | 31.3 | — | Yes |
| local | 1000 | 2000 | 400 | 3.7 | 4.4 | 0 | 37.1 | — | Yes |
| subprocess | 500 | 1000 | 200 | 4.9 | 5.4 | 0 | 12.1 | 19.6 | Yes |
| subprocess | 750 | 1500 | 300 | 3.9 | 4.4 | 0 | 13.6 | 24.3 | Yes |
| subprocess | 1000 | 2000 | 400 | 3.6 | 4.1 | 0 | 14.8 | 30.3 | Yes |

Reproduce independently for each placement from the repository root.

```sh
python benchmarks/kajennspa/run.py local --levels 500,750,1000 --max-pages 2000 --cycles 6 --idle-seconds 5 --output local-extended.json
python benchmarks/kajennspa/run.py subprocess --levels 500,750,1000 --max-pages 2000 --cycles 6 --idle-seconds 5 --output subprocess-extended.json
```

Raw measurements include setup p95, idle ping counts, p99, error counts, CPU and sampled peak RSS for each process. [local JSON](results/2026-11-24-local-extended.json), [subprocess JSON](results/2026-11-24-subprocess-extended.json).

### Five times the traffic

2,000 registered pages, twenty cycles one second apart and a three-second idle window.

| Placement | Users | WS open | Offered ops/s | Bind p95 ms | RPC p95 ms | Missing | Front CPU % | App CPU % | Pass |
|---|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| local | 250 | 500 | 500 | 2.6 | 3.4 | 0 | 34.9 | — | Yes |
| local | 500 | 1000 | 1000 | 1.7 | 2.5 | 0 | 50.9 | — | Yes |
| local | 750 | 1500 | 1500 | 170.2 | 312.8 | 0 | 81.1 | — | No |
| subprocess | 250 | 500 | 500 | 3.5 | 3.9 | 0 | 19.8 | 28.6 | Yes |
| subprocess | 500 | 1000 | 1000 | 1.9 | 2.1 | 0 | 27.6 | 45.0 | Yes |
| subprocess | 750 | 1500 | 1500 | 21.2 | 37.0 | 0 | 36.8 | 66.5 | Yes |
| subprocess | 1000 | 2000 | 2000 | 1143.5 | 4378.7 | 0 | 44.0 | 89.1 | No |

Reproduce independently for each placement from the repository root.

```sh
python benchmarks/kajennspa/run.py local --levels 250,500,750,1000 --max-pages 2000 --interval 1 --cycles 20 --idle-seconds 3 --output local-busy.json
python benchmarks/kajennspa/run.py subprocess --levels 250,500,750,1000 --max-pages 2000 --interval 1 --cycles 20 --idle-seconds 3 --output subprocess-busy.json
```

Raw measurements include setup p95, idle ping counts, p99, error counts, CPU and sampled peak RSS for each process. [local JSON](results/2026-11-24-local-busy.json), [subprocess JSON](results/2026-11-24-subprocess-busy.json).

### Independent hold at 750 active users

Each placement started fresh and held 1,500 operations/s for one minute following setup.

| Placement | Users | WS open | Offered ops/s | Bind p95 ms | RPC p95 ms | Missing | Front CPU % | App CPU % | Pass |
|---|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| local | 750 | 1500 | 1500 | 169.0 | 323.9 | 0 | 80.8 | — | No |
| subprocess | 750 | 1500 | 1500 | 31.5 | 55.1 | 0 | 37.5 | 66.1 | Yes |

Reproduce independently for each placement from the repository root.

```sh
python benchmarks/kajennspa/run.py local --levels 750 --max-pages 2000 --interval 1 --cycles 60 --idle-seconds 3 --output local-repeat.json
python benchmarks/kajennspa/run.py subprocess --levels 750 --max-pages 2000 --interval 1 --cycles 60 --idle-seconds 3 --output subprocess-repeat.json
```

Raw measurements include setup p95, idle ping counts, p99, error counts, CPU and sampled peak RSS for each process. [local JSON](results/2026-11-24-local-repeat.json), [subprocess JSON](results/2026-11-24-subprocess-repeat.json).

## Capacity planning

With two tabs per user, the default 1,000-page limit admits up to 500 such users if no other pages occupy the dispatcher. The dispatcher checks the number of registered pages after pruning. A retained page can still occupy a slot after its tab disconnects. The raised limit applies only to this fixture.

Each run used a minimal in-memory application and a private store per user. Large fan-out, application queries, sustained sessions, connection churn and off-host transport need separate measurements. Subprocess placement here kept the public server and authentication in the front process and placed the Gramlot application in a separate process on the same machine. Orchestra was outside the measured configurations. CPU percentages use one logical CPU as 100%.

The 1,000-user, five-second run delivered all 12,000 scheduled operations in each placement. In process, the server peaked at 371 MiB RSS during the active window. In subprocess mode the front peaked at 287 MiB and the application at 224 MiB. At this level the p99 RPC latencies were 94.7 and 43.7 ms respectively. A single short run per level does not establish a production limit. Use the observed range to select a longer test with the application’s real callbacks, store sizes and simultaneous edits before a migration decision.
