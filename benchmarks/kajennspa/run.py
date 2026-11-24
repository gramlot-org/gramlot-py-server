"""Measure one Kajenn SPA placement on loopback. All users and stores are disposable."""

import argparse
import asyncio
import json
import math
import os
import platform
import re
import secrets
import signal
import subprocess
import sys
import tempfile
import time
from collections import Counter
from contextlib import AsyncExitStack
from importlib.metadata import version
from pathlib import Path

import httpx
import psutil
from cryptography.fernet import Fernet
from websockets.asyncio.client import connect

CLOCK = time.monotonic


def stats(samples):
    if not samples:
        return {}
    ordered = sorted(samples)
    return {
        f"p{q}": round(1000 * ordered[math.ceil(len(ordered) * q / 100) - 1], 1)
        for q in (50, 95, 99)
    }


def envelope(pid, name, marker, source=False):
    return {
        "pageId": pid,
        "id": marker,
        "name": name,
        "contentType": "source" if source else "data",
        "params": {} if source else {"marker": marker},
    }


class Tab:
    def __init__(self, pid, ws):
        self.pid = pid
        self.ws = ws

    async def send(self, message):
        await self.ws.send(json.dumps({"pageId": self.pid, **message}))

    async def receive(self):
        data = json.loads(await self.ws.recv())
        if data.get("pageId") != self.pid or "error" in data:
            raise ValueError("Invalid server envelope")
        return data


async def open_user(base, index, password, stack, tab_count):
    tabs = []
    async with httpx.AsyncClient(base_url=base, trust_env=False, timeout=10) as client:
        response = await client.post(
            "/_auth/login", json={"identity": f"u{index}", "password": password}
        )
        response.raise_for_status()
        if response.json().get("identity") != f"u{index}":
            raise ValueError("Login identity mismatch")
        for i in range(tab_count):
            response = await client.get("/bench/pages/")
            response.raise_for_status()
            bootstrap = json.loads(re.search(r"new PageBootstrap\((.+)\)\.run", response.text)[1])[
                "config"
            ]
            pid = bootstrap["pageId"]
            source = await client.post(
                bootstrap["rpcUrl"], json=envelope(pid, "main", f"main{i}", True)
            )
            source.raise_for_status()
            if not source.json().get("value"):
                raise ValueError("Page rendering failed")
            address = base.replace("http:", "ws:") + bootstrap["websocketUrl"] + "?pageId=" + pid
            cookie = "; ".join(f"{k}={v}" for k, v in client.cookies.items())
            ws = await stack.enter_async_context(
                connect(
                    address,
                    origin=base,
                    additional_headers={"Cookie": cookie},
                    proxy=None,
                    open_timeout=10,
                    close_timeout=1,
                )
            )
            tab = Tab(pid, ws)
            await tab.send({"op": "subscribe", "binderId": "editor", "path": "editor"})
            if (await tab.receive()).get("op") != "snapshot":
                raise ValueError("Missing initial snapshot")
            tabs.append(tab)
    if len({tab.pid for tab in tabs}) != tab_count:
        raise ValueError("Duplicate page ID in session")
    return tabs


async def operation(user, index, sequence, kind):
    a = user[0]
    marker = f"{index}-{sequence}-{kind}"
    if kind == "bind":
        await a.send(
            {
                "op": "change",
                "binderId": "editor",
                "path": "",
                "evt": "upd_value",
                "value": marker,
                "attr": {},
            }
        )

        async def check_peer(peer):
            msg = await peer.receive()
            if msg.get("binderId") != "editor" or msg.get("value") != marker:
                raise ValueError("Peer value mismatch")

        if len(user) == 2:
            await check_peer(user[1])
        else:
            async with asyncio.TaskGroup() as group:
                for peer in user[1:]:
                    group.create_task(check_peer(peer))
    else:
        await a.send(envelope(a.pid, "echo", marker))
        while True:
            response = await a.receive()
            if "id" in response:
                if response["id"] != marker or response.get("value") != {
                    "marker": marker,
                    "user": f"u{index}",
                }:
                    raise ValueError("RPC reply mismatch")
                break


def snapshot(process):
    cpu = process.cpu_times()
    return cpu.user + cpu.system, process.memory_info().rss / 2**20


async def level(users, args, processes, *, idle=False):
    n = len(users)
    values = {"bind": [], "rpc": []}
    errors = Counter()
    start = CLOCK()
    resources = {k: snapshot(p) for k, p in processes.items()}
    peaks = {k: v[1] for k, v in resources.items()}
    duration = args.idle_seconds if idle else args.cycles * args.interval

    async def sample():
        while True:
            for k, p in processes.items():
                peaks[k] = max(peaks[k], snapshot(p)[1])
            await asyncio.sleep(0.5)

    monitor = asyncio.create_task(sample())

    async def exercise(i, user, kind):
        phase = (i / n + (0.5 if kind == "rpc" else 0)) % 1
        for j in range(args.cycles):
            due = start + (j + phase) * args.interval
            await asyncio.sleep(max(0, due - CLOCK()))
            try:
                async with asyncio.timeout(max(0.001, due + args.timeout - CLOCK())):
                    await operation(user, i, j, kind)
                values[kind].append(CLOCK() - due)
            except Exception as err:
                errors[f"{kind}:{type(err).__name__}"] += 1
                return

    try:
        if not idle:
            await asyncio.gather(
                *(exercise(i, user, kind) for i, user in enumerate(users) for kind in values)
            )
        await asyncio.sleep(max(0, start + duration - CLOCK()))
    finally:
        monitor.cancel()
        await asyncio.gather(monitor, return_exceptions=True)
    elapsed = CLOCK() - start
    usage = {}
    for name, p in processes.items():
        cpu, rss = snapshot(p)
        usage[name] = {
            "cpu_percent": round(100 * (cpu - resources[name][0]) / elapsed, 1),
            "rss_peak_mib": round(max(rss, peaks[name]), 1),
        }
    alive = sum(tab.ws.close_code is None for user in users for tab in user)
    expected = 0 if idle else n * args.cycles
    measures = {
        kind: {"ok": len(v), "missing": expected - len(v), **stats(v)} for kind, v in values.items()
    }
    passed = alive == args.tabs_per_user * n and all(
        m["missing"] == 0 and m.get("p95", 0) <= args.slo_ms for m in measures.values()
    )
    if idle:
        semaphore = asyncio.Semaphore(16)

        async def ping(tab):
            async with semaphore:
                try:
                    async with asyncio.timeout(args.timeout):
                        await (await tab.ws.ping())
                    return True
                except Exception as err:
                    errors["ping:" + type(err).__name__] += 1
                    return False

        pongs = await asyncio.gather(*(ping(tab) for user in users for tab in user))
        passed = passed and all(pongs)
    return {
        "users": n,
        "sockets": args.tabs_per_user * n,
        "sockets_open_at_end": alive,
        "window_s": round(elapsed, 2),
        "pongs": sum(pongs) if idle else None,
        "expected_per_operation": expected,
        "operations": measures,
        "errors": dict(errors),
        "resources": usage,
        "passed": passed,
    }


async def run(args):
    levels = args.levels
    result = {
        "placement": args.placement,
        "tabs_per_user": args.tabs_per_user,
        "levels": levels,
        "cycles": args.cycles,
        "interval_s": args.interval,
        "idle_seconds": args.idle_seconds,
        "idle_only": args.idle_only,
        "slo_ms": args.slo_ms,
        "timeout_s": args.timeout,
        "setup_parallel": args.ramp,
        "host": platform.platform(),
        "logical_cpus": psutil.cpu_count(),
        "ram_gib": round(psutil.virtual_memory().total / 2**30, 1),
        "python": platform.python_version(),
        "packages": {
            p: version(p)
            for p in ("kajenn", "gramlot", "gramlot-py-server", "uvicorn", "websockets")
        },
        "stages": [],
    }

    def save():
        args.output.write_text(json.dumps(result, indent=2) + "\n")

    with tempfile.TemporaryDirectory(prefix="kajenn-load-") as folder:
        root = Path(folder)
        password = secrets.token_urlsafe(24)
        env = {
            **os.environ,
            "BENCH_PASSWORD": password,
            "BENCH_KEY": Fernet.generate_key().decode(),
            "BENCH_USERS": str(max(levels)),
            "BENCH_HOME": folder,
            "BENCH_MODE": args.placement,
            "BENCH_PAGE_LIMIT": str(args.max_pages or ""),
        }
        with (root / "server.log").open("w") as log:
            process = subprocess.Popen(
                [sys.executable, str(Path(__file__).with_name("serve.py").resolve())],
                cwd=root,
                env=env,
                stdout=log,
                stderr=log,
                start_new_session=True,
            )
            stacks = []
            try:
                async with asyncio.timeout(90):
                    while not (root / "port").is_file():
                        if process.poll() is not None:
                            raise RuntimeError("Server exited before listening")
                        await asyncio.sleep(0.1)
                    base = "http://127.0.0.1:" + (root / "port").read_text()
                    async with httpx.AsyncClient(base_url=base, trust_env=False) as client:
                        while True:
                            if process.poll() is not None:
                                raise RuntimeError("Server exited during startup")
                            try:
                                r = await client.get("/bench/ready")
                                if r.status_code == 200:
                                    break
                            except httpx.TransportError:
                                pass
                            await asyncio.sleep(0.2)
                processes = {
                    "front": psutil.Process(process.pid),
                    "driver": psutil.Process(),
                }
                result["max_pages"] = r.json()["max_pages"]
                pid = r.json()["pid"]
                if args.placement == "subprocess":
                    assert pid != process.pid
                    processes["app"] = psutil.Process(pid)
                else:
                    assert pid == process.pid
                result["baseline_rss_mib"] = {
                    k: round(snapshot(p)[1], 1) for k, p in processes.items()
                }
                users = []
                for target in levels:
                    setup_times = []
                    setup_errors = Counter()
                    since = CLOCK()

                    async def add(index):
                        stack = AsyncExitStack()
                        stacks.append(stack)
                        ts = CLOCK()
                        try:
                            async with asyncio.timeout(30):
                                tabs = await open_user(
                                    base, index, password, stack, args.tabs_per_user
                                )
                            setup_times.append(CLOCK() - ts)
                            return tabs
                        except Exception as err:
                            desc = type(err).__name__
                            if isinstance(err, httpx.HTTPStatusError):
                                desc += f" HTTP {err.response.status_code}"
                            elif isinstance(err, ValueError):
                                desc += " " + str(err)[:60]
                            setup_errors[desc] += 1

                    setup_peaks = {name: snapshot(proc)[1] for name, proc in processes.items()}

                    async def sample_setup():
                        while True:
                            for name, proc in processes.items():
                                setup_peaks[name] = max(setup_peaks[name], snapshot(proc)[1])
                            await asyncio.sleep(0.1)

                    sampler = asyncio.create_task(sample_setup())
                    try:
                        for first in range(len(users), target, args.ramp):
                            batch = await asyncio.gather(
                                *(add(i) for i in range(first, min(first + args.ramp, target)))
                            )
                            users.extend(pair for pair in batch if pair is not None)
                            if setup_errors:
                                break
                    finally:
                        sampler.cancel()
                        await asyncio.gather(sampler, return_exceptions=True)
                    setup = {
                        "p_ms": stats(setup_times),
                        "rss_peak_mib": {
                            name: round(max(peak, snapshot(processes[name])[1]), 1)
                            for name, peak in setup_peaks.items()
                        },
                        "seconds": round(CLOCK() - since, 2),
                        "errors": dict(setup_errors),
                    }
                    if setup_errors:
                        result["stages"].append(
                            {
                                "requested": target,
                                "complete_users": len(users),
                                "setup": setup,
                                "passed": False,
                            }
                        )
                        save()
                        break
                    idle_row = await level(users, args, processes, idle=True)
                    if args.idle_only or not idle_row["passed"]:
                        row = idle_row
                    else:
                        row = await level(users, args, processes)
                        row["idle"] = idle_row
                    row["setup"] = setup
                    result["stages"].append(row)
                    save()
                    print(json.dumps(row), flush=True)
                    if not row["passed"]:
                        break
            finally:
                for first in range(0, len(stacks), 16):
                    await asyncio.gather(
                        *(s.aclose() for s in stacks[first : first + 16]),
                        return_exceptions=True,
                    )
                if process.poll() is None:
                    process.terminate()
                    try:
                        await asyncio.to_thread(process.wait, 10)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                save()
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("placement", choices=["local", "subprocess"])
    p.add_argument(
        "--tabs-per-user",
        type=int,
        default=2,
        help="one foreground sender, remaining pages receive updates",
    )
    p.add_argument("--max-pages", type=int, help="override the dispatcher page limit")
    p.add_argument("--levels", default="8,16,32,64,128,256,500")
    p.add_argument("--cycles", type=int, default=4)
    p.add_argument("--interval", type=float, default=5)
    p.add_argument("--ramp", type=int, default=8)
    p.add_argument("--slo-ms", type=float, default=250)
    p.add_argument("--timeout", type=float, default=5)
    p.add_argument("--idle-seconds", type=float, default=8)
    p.add_argument("--idle-only", action="store_true")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    args.levels = list(map(int, args.levels.split(",")))
    if args.tabs_per_user < 2:
        p.error("--tabs-per-user must be at least 2 for cross-tab binding")
    if args.max_pages is not None and args.max_pages < 1:
        p.error("--max-pages must be positive")
    if (
        args.levels != sorted(set(args.levels))
        or min(
            *args.levels,
            args.cycles,
            args.ramp,
            args.interval,
            args.timeout,
            args.slo_ms,
            args.idle_seconds,
        )
        <= 0
    ):
        p.error("levels must be strictly increasing and all workload settings positive")
    result = asyncio.run(run(args))
    sys.exit(0 if all(stage["passed"] for stage in result["stages"]) else 1)
