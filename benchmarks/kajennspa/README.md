# Kajenn SPA load test

Compare an in-process Gramlot application with the same application hosted by Kajenn's subprocess spawner. The driver always creates a disposable site bound to loopback. The driver is a separate process in both configurations. In subprocess mode the driver verifies that a request executes under a different PID from the front server.

## Run

Use a Python 3.12 environment with the compatible Kajenn, Gramlot core and Gramlot Python Server builds installed. The core needs its normal generated browser assets. Install the server’s Kajenn extra, plus `httpx`, `psutil`, `cryptography`, `uvicorn` with the `websockets-sansio` backend, and a `websockets.asyncio` client with the `proxy` option. The recorded runs include the package versions. See [the measured results](RESULTS.md) for the reference host.

Run these commands separately, on an otherwise comparable host:

```sh
python benchmarks/kajennspa/run.py local --levels 16,64,128,256,384,500 --output local.json
python benchmarks/kajennspa/run.py subprocess --levels 16,64,128,256,384,500 --output subprocess.json
```

Each stage retains the preceding stage's sessions and sockets. One synthetic user logs in through `/_auth/login`, opens two pages under the same session, invokes their real `main` RPC, opens two native WebSockets, and subscribes both to an authorized shared value scoped to that user. The load driver speaks the Gramlot wire protocol directly. It does not render the DOM or download static assets.

The default stage has an eight-second idle window followed by a ping/pong check on every socket. During the active window each user makes one change on tab A and waits for the matching value on tab B, and makes one echo RPC checked for both payload and identity, every five seconds. Arrivals are staggered across users. Four cycles give a twenty-second active window. Setup timings cover login and opening both tabs. Setup is measured separately from steady-state traffic.

Latency is measured from the scheduled arrival time through the validated reply, including driver delay. A stage passes when all sockets stay open, every expected operation completes correctly, and both p95 latencies are at most 250 ms. A failed operation aborts the affected stream for that user; every remaining expected operation on that stream is counted as missing. The run stops after the first failed setup or stage. The driver exits with status 1 on a failed stage and records the failure in the JSON output.

Use `--cycles` for a longer hold, `--interval` to change the per-user rate, `--slo-ms` to supply an application-specific objective, and `--idle-only --idle-seconds 60` to measure mostly idle connections. Change `--ramp` to vary concurrent logins during setup. Use `--max-pages 2000` to allow 1,000 two-tab users on the disposable dispatcher. Each invocation starts fresh processes and storage. No real user, token or production endpoint is needed.

## One foreground page per user

Set `--tabs-per-user` to the number of live pages for each authenticated user (default 2). Only the first page sends application traffic. All other pages keep a WebSocket open and receive the same user's shared-store changes. A binding operation completes once the last background page has received and validated the value. The setup phase samples process RSS every 100 ms, including login and opening all pages.

```sh
python benchmarks/kajennspa/run.py local --levels 10 --tabs-per-user 10 --interval 1 --cycles 30 --output ten-pages.json
python benchmarks/kajennspa/run.py local --levels 10 --tabs-per-user 20 --interval 1 --cycles 30 --output twenty-pages.json
```

## Interpret

Two tabs mean **two physical WebSockets and two logical pages per user**. The standard dispatcher allows 1,000 pages by default. This gives a configuration ceiling of 500 simultaneous users for this exact two-tab profile, independently of latency. CPU percentages are process CPU time divided by wall time (100% is one logical CPU). RSS includes shared pages, so adding RSS from different processes can overstate unique memory use.

Read the results alongside the application workload. Real database queries, CPU-heavy controllers, many subscribers to the same store, login bursts, long sessions, TLS and WAN latency can change the outcome. A local subprocess is not a second machine. Compare repeat runs near the first failure before treating it as a capacity boundary; an idle connection count alone does not measure interactive capacity.
