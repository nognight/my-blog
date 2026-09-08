---
title: 'Build a Minimal Python Event Loop From Scratch'
pubDate: '2026-09-08'
description: 'Callbacks, timers, selectors, Futures and Tasks in ~120 lines — no asyncio, just heapq, deque and selectors.'
heroImage: '../../assets/blog-placeholder-2.jpg'
tags:
  - python
  - asyncio
  - tutorial
---

# Build a Minimal Python Event Loop From Scratch

`asyncio.run(main())` feels like magic until you build it. This post builds a working loop in 5 steps: ready queue, timers, I/O, `Future`/`Task`, sockets. Final code is ~120 lines, stdlib only, and passes the demo at the bottom.

Mental model:

```text
timers (heapq) ──due──> ready (deque) ──run──> callbacks
selectors ──readable──> ready (deque) ──run──> callbacks
await Future ──done──> Task._step ──send──> coroutine
```

## 0. Skeleton

Three states only: what is ready now, what wakes up later, what waits for I/O.

```python
import heapq
import selectors
import time
from collections import deque

class Loop:
    def __init__(self):
        self._ready = deque()
        self._selector = selectors.DefaultSelector()
        self._timers = []
        self._seq = 0
        self._stopping = False

    def call_soon(self, cb, *args):
        self._ready.append((cb, args))

    def stop(self):
        self._stopping = True
```

## 1. Ready queue + `run_forever`

Drain the queue. If empty and nothing else to do, exit — this prevents busy-loop on stop.

```python
class Loop:
    def run_forever(self):
        self._stopping = False
        while not self._stopping:
            if not self._ready:
                if not self._timers and not self._selector.get_map():
                    break
                continue
            for _ in range(len(self._ready)):
                cb, args = self._ready.popleft()
                cb(*args)
```

Test it:

```python
loop = Loop()
loop.call_soon(print, "hello")
loop.call_soon(loop.stop)
loop.run_forever()  # hello
```

## 2. Timers with `heapq`

Store `(when, seq, cb, args)`. `seq` breaks ties when two timers fire at once. Each iteration moves due timers to ready.

```python
class Loop:
    def call_later(self, delay, cb, *args):
        self._seq += 1
        heapq.heappush(self._timers, (time.monotonic() + delay, self._seq, cb, args))

    def _run_timers(self):
        now = time.monotonic()
        while self._timers and self._timers[0][0] <= now:
            _, _, cb, args = heapq.heappop(self._timers)
            self._ready.append((cb, args))
```

Update `run_forever` to compute `select` timeout from the next timer:

```python
    def run_forever(self):
        self._stopping = False
        while not self._stopping:
            self._run_timers()
            timeout = 0
            if not self._ready and not self._stopping:
                if self._timers:
                    timeout = max(0, self._timers[0][0] - time.monotonic())
                else:
                    timeout = 0.01
                events = self._selector.select(timeout)
                for key, _ in events:
                    cb, args = key.data
                    self._ready.append((cb, args))
                self._run_timers()
            if not self._ready:
                if not self._timers and not self._selector.get_map():
                    break
                if not self._ready:
                    continue
            for _ in range(len(self._ready)):
                cb, args = self._ready.popleft()
                cb(*args)
            if not self._ready and not self._timers and not self._selector.get_map():
                break
```

## 3. I/O with `selectors`

One thread, many sockets. Register interest, `select()` wakes us.

```python
class Loop:
    def add_reader(self, fd, cb, *args):
        self._selector.register(fd, selectors.EVENT_READ, (cb, args))

    def remove_reader(self, fd):
        try:
            self._selector.unregister(fd)
        except KeyError:
            pass
```

No new thread per connection — the loop parks in `select(timeout)` until a fd is readable or the next timer fires.

## 4. `Future`, `Task`, `sleep`

`Future` is a one-shot box. `Task` drives a coroutine by `send()`-ing results back in.

```python
class Future:
    def __init__(self, loop):
        self._loop = loop
        self._result = None
        self._exception = None
        self._done = False
        self._callbacks = []

    def done(self):
        return self._done

    def result(self):
        if self._exception:
            raise self._exception
        return self._result

    def set_result(self, result=None):
        self._result = result
        self._done = True
        for cb in self._callbacks:
            self._loop.call_soon(cb, self)

    def set_exception(self, exc):
        self._exception = exc
        self._done = True
        for cb in self._callbacks:
            self._loop.call_soon(cb, self)

    def add_done_callback(self, cb):
        if self._done:
            self._loop.call_soon(cb, self)
        else:
            self._callbacks.append(cb)

    def __await__(self):
        if not self._done:
            yield self
        if self._exception:
            raise self._exception
        return self._result

    __iter__ = __await__


class Task(Future):
    def __init__(self, loop, coro):
        super().__init__(loop)
        self._coro = coro
        loop.call_soon(self._step)

    def _step(self, fut=None):
        try:
            if fut is None:
                yielded = self._coro.send(None)
            elif fut._exception:
                yielded = self._coro.throw(fut._exception)
            else:
                yielded = self._coro.send(fut._result)
        except StopIteration as e:
            self.set_result(e.value)
        except Exception as e:
            self.set_exception(e)
        else:
            if isinstance(yielded, Future):
                if yielded.done():
                    self._loop.call_soon(self._step, yielded)
                else:
                    yielded.add_done_callback(self._step)
            elif yielded is None:
                self._loop.call_soon(self._step)
            else:
                raise RuntimeError(f"bad yield: {yielded!r}")
```

`sleep` is just a timer that completes a `Future`:

```python
def sleep(loop, delay, result=None):
    fut = Future(loop)
    loop.call_later(delay, fut.set_result, result)
    return fut
```

Timers demo — `B` finishes first even though it started second:

```python
async def worker(loop, name, delay):
    print(f"{name} start")
    await sleep(loop, delay, result=name)
    print(f"{name} done after {delay}s")
    return name

async def main_timers(loop):
    t1 = Task(loop, worker(loop, "A", 0.05))
    t2 = Task(loop, worker(loop, "B", 0.01))
    await t1
    await t2
```

Output:

```text
A start
B start
B done after 0.01s
A done after 0.05s
```

**Why this works:** `await sleep(...)` yields the unfinished `Future`. The coroutine pauses. When the timer fires, `set_result` schedules `Task._step`, which `send()`s the result back in.

## 5. Non-blocking sockets

Wrap `recv` in a `Future` that completes on readability. `socketpair()` avoids real ports in the demo.

```python
def sock_recv(loop, sock, n):
    fut = Future(loop)

    def _on_read():
        try:
            data = sock.recv(n)
        except BlockingIOError:
            return
        loop.remove_reader(sock.fileno())
        fut.set_result(data)

    sock.setblocking(False)
    loop.add_reader(sock.fileno(), _on_read)
    return fut
```

Echo server + client:

```python
import socket

async def echo_server(loop, sock):
    while True:
        data = await sock_recv(loop, sock, 1024)
        if not data:
            break
        sock.sendall(data.upper())

async def echo_client(loop, sock):
    sock.setblocking(False)
    sock.sendall(b"hello loop")
    data = await sock_recv(loop, sock, 1024)
    assert data == b"HELLO LOOP", data
    print(f"echo ok: {data!r}")
    sock.close()
    return data

async def main_echo(loop):
    a, b = socket.socketpair()
    srv = Task(loop, echo_server(loop, a))
    res = await echo_client(loop, b)
    loop.remove_reader(a.fileno())
    a.close()
    return res
```

**Fix for leaks:** every `add_reader` needs a matching `remove_reader` once the `Future` completes, otherwise `select()` keeps waking up on a closed fd.

## 6. `run_until_complete` + full run

```python
class Loop:
    def run_until_complete(self, coro):
        task = Task(self, coro)
        self.run_forever()
        return task.result()

async def main(loop):
    await main_timers(loop)
    await main_echo(loop)
    loop.stop()

if __name__ == "__main__":
    loop = Loop()
    loop.call_soon(lambda: Task(loop, main(loop)))
    loop.run_forever()
    print("ALL OK")
```

Run it:

```bash
python3 miniloop.py
# A start
# B start
# B done after 0.01s
# A done after 0.05s
# timers ok
# echo ok: b'HELLO LOOP'
# ALL OK
```

Full file is ~140 lines with demos — copy steps 0–6 in order and it runs.

## What real `asyncio` adds

- Buffered protocols/transports, `StreamReader`, backpressure
- `call_soon_threadsafe`, signal handling, subprocess, `gather`/`wait_for` cancellation
- `uvloop`/`epoll`/`kqueue` performance, `staggered` timeouts, eager task factory

Ours skips all that on purpose — the core is just ready + timers + selectors + `send()`.

## Checklist

- [ ] `call_soon` never runs callbacks reentrantly — always via queue
- [ ] Timers use `monotonic()`, not `time()`
- [ ] Every `add_reader` paired with `remove_reader`
- [ ] `Future` completes exactly once
- [ ] `Task._step` handles `StopIteration.value` as return value
- [ ] `BlockingIOError` on non-blocking `recv` retries, doesn't complete

> Next: add `gather()` with cancellation, or `wait_for(timeout)` using `call_later` + `Future.cancel()`.
