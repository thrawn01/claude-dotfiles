---
name: surface-testing
description: Write surface tests that exercise the system through its surface — the outermost layer consumers interact with (HTTP endpoints, CLI entry points, exported functions). Never test internal functions directly. Expose observability APIs when async behavior isn't visible at the surface.
---

# Surface Testing

## Why This Matters

A well-written test should never need to change unless the system's requirements change. There are four kinds of changes engineers make to production code:

- **Pure refactoring** (renaming, restructuring, optimizing internals): tests should NOT break
- **New features** (adding behavior): existing tests should NOT break; write new tests
- **Bug fixes** (covering missing cases): existing tests should NOT break; add the missing test
- **Behavior changes** (altering what the system does): tests SHOULD break — this is the only valid reason

If your tests break during a refactoring, they are coupled to implementation, not behavior. This skill prevents that by enforcing one rule: **always test through the surface.**

The "surface" is the outermost layer consumers interact with — HTTP endpoints, CLI entry points, exported functions. Tests that enter through the surface verify behavior. Tests that reach into internals verify implementation. The first kind survives refactoring. The second kind doesn't.

## Core Rule

**Every test must interact with the system the same way its end users would.** Never call internal/private functions directly in tests. If you can't observe a behavior through the surface, that's a design signal — fix the design, not the test strategy.

## Finding the Surface

Before writing tests, identify the public interface:

- **HTTP/gRPC API**: the endpoints. Boot the full application and make real HTTP requests. Do not instantiate controllers, handlers, or services directly.
- **CLI**: the `Run()` function. Call it with arguments and capture output. Do not call subcommand handlers or internal functions directly.
- **Library**: the exported/public functions. Call them the way a consumer would. Do not call unexported/private functions.
- **Internal Library Boundary**: a package within the codebase that exposes a complete, self-contained API — structurally identifiable by whether it could be extracted and published independently without changing its interface. In all contexts — design, implementation, and review — recognize or introduce these boundaries at domain edges and test each through its own exported interface only. Consumers use the real package; there is nothing to substitute unless the package itself wraps an external dependency.

This applies especially to libraries with complex internals — parsers are the classic case, where it's tempting to test the tokenizer or state machine directly. Don't.

> **True story.** A MIME parser accumulated 3,000 tests against its public `Parse()` over years of real-world edge cases. A later rewrite from recursive-descent to a stateful non-recursive implementation was validated end-to-end by those same tests — proving correctness and a speedup. Tests against the recursive internals would have been thrown away with the recursion, giving no signal about equivalence. Surface tests outlived the implementation.

### I found an unexported/private function I want to test. What do I do?
Don't test it directly. Trace backward: which public entry point exercises this function? Write your test through that entry point instead. If no public entry point reaches this code, either the code is dead and should be removed, or the design needs to change to make the behavior reachable.

### The behavior I want to test spans multiple services.
Pick the entry point that a real user would trigger. If a user submits an order via the Order Service and that produces an event consumed by the Billing Service, the test enters through the Order Service's HTTP API and asserts the downstream effect (using fakes to capture cross-service communication).

## Structuring Code for Testability

The surface must be reachable by tests. This often requires a small structural change: make the application's entry point callable from test code.

### CLI Applications (Go)

Make `main()` a thin wrapper that delegates to a testable `Run()` function:

```go
// main.go
package main

import (
    "os"
    "github.com/your/project/cmd"
)

func main() {
    os.Exit(cmd.Run(os.Args[1:], cmd.RunOptions{
        Stdout: os.Stdout,
        Stderr: os.Stderr,
    }))
}
```

The `Run()` function accepts arguments and injected dependencies. This IS the surface — both `main()` and tests enter through it:

```go
// cmd/run.go
package cmd

type RunOptions struct {
    Stdout io.Writer
    Stderr io.Writer
}

func Run(args []string, opts RunOptions) int {
    // All application logic lives here
}
```

Tests call `Run()` with test arguments and capture output:

```go
func TestSubCommand(t *testing.T) {
    var stdout bytes.Buffer
    exitCode := cmd.Run([]string{"sub-command", "-f", "filename.ext"}, cmd.RunOptions{
        Stdout: &stdout,
    })
    require.Equal(t, 0, exitCode)
    assert.Contains(t, stdout.String(), "expected output")
}
```

### HTTP Services (Go)

Start a real server in tests and make real HTTP requests:

```go
func TestCreateUser(t *testing.T) {
    // Given: a running server
    server := api.NewServer(api.ServerOptions{ /* inject real or test deps */ })
    go server.Start("localhost:0")
    defer server.Shutdown()

    // When: creating a user via HTTP
    resp, err := http.Post(server.URL()+"/users", "application/json",
        strings.NewReader(`{"name":"Alice"}`))
    require.NoError(t, err)
    defer resp.Body.Close()

    // Then: the response confirms creation
    assert.Equal(t, http.StatusCreated, resp.StatusCode)
}
```

### HTTP Services (Kotlin/Micronaut)

**Wrong approach** — testing a service in isolation, mocking its dependencies, and verifying internal method calls. Breaks on any refactor even if API behavior is unchanged:

```kotlin
// DON'T DO THIS
class UserServiceTest {
    private val repository = mockk<UserRepository>()
    private val service = UserService(repository)

    @Test fun `should create user`() {
        every { repository.save(any()) } returns User("Alice")
        val result = service.createUser("Alice")
        assertEquals("Alice", result.name)
        verify { repository.save(any()) }
    }
}
```

**Right approach** — boot the full application via `@MicronautTest` and go through HTTP:

```kotlin
@MicronautTest
class UserControllerTest {
    @Inject lateinit var client: HttpClient

    @Test fun `should create user`() {
        val response = client.toBlocking().exchange(
            HttpRequest.POST("/users", mapOf("name" to "Alice")),
            Map::class.java)
        assertEquals(HttpStatus.CREATED, response.status)
    }
}
```

`@MicronautTest` starts the full application context. The test enters through the same HTTP endpoint a real client would use. Use `@MockBean` or `@Replaces` ONLY for external boundaries (third-party APIs, payment gateways) — never for internal services.

## When the "Then" Breaks: Testing Async Behavior

Sometimes you write a test and get stuck at the assertion. You called the endpoint, the request succeeded, but the real work happens asynchronously. The "then" is empty.

**This is a design problem, not a testing problem. Fix the design, not the test strategy.**

### First: Assert Downstream Effects

Most async operations produce observable downstream results. Test those results through the public interface:

```go
func TestOrderProcessing(t *testing.T) {
    // Given: a running server
    server := api.NewServer(api.ServerOptions{})
    go server.Start("localhost:0")
    defer server.Shutdown()

    // When: submitting an order
    resp, err := http.Post(server.URL()+"/orders", "application/json",
        strings.NewReader(`{"item":"widget","qty":5}`))
    require.NoError(t, err)
    assert.Equal(t, http.StatusAccepted, resp.StatusCode)

    // Then: the order appears in the billing system
    require.Eventually(t, func() bool {
        bills, _ := http.Get(server.URL() + "/billing/pending")
        // parse and check for our order
        return containsOrder(bills, "widget", 5)
    }, time.Second, 10*time.Millisecond)
}
```

The async work resulted in a billing record. That's observable through the public interface. No special APIs needed — just poll the downstream result.

### Substituting External Dependencies: Prefer Real Fakes

When behavior produces output to an external system — an object store, message broker, email service, payment gateway — you need to substitute that dependency so tests are hermetic. The question is *how much of the production code path stays in play*. The more real stack a test exercises — real TCP, real HTTP client, real serialization, real connection pooling — the more production bugs it can catch.

A **real fake** is a faithful reimplementation of the external service's protocol. Your application talks to it over the same wire protocol it would use in production, exercising the same client library, codec paths, and connection handling. A **hand-written fake** substitutes those away — it encodes *your understanding* of how the service behaves, and when that understanding is incomplete or drifts, tests pass while production breaks.

Prefer substitutes in this order, ranked by how much of the real stack they preserve:

1. **In-process fake library** in your language — fastest, exercises the real protocol, no external process.
2. **Testcontainers running a published fake container** — exercises the real protocol across a real network hop; slower startup.
3. **Hand-written fake** — only when no published substitute exists for the service.

> **True story.** A team used a real Go DNS server in their tests; their service made actual DNS calls against it. A new Go version changed resolver behavior subtly, and the test suite caught the regression before deploy. A mocked resolver would have shipped the bug. That's the payoff of keeping the real stack in play.

**What counts as "external"?** Any service outside the deployment unit the test exercises. If five microservices live in the same repo, a test of service A still substitutes B through E — the test's job is to verify *this* service, not the others. If a dependent service is in the same language and ships an embedded constructor, that's the highest-fidelity substitute — see below.

Never substitute components *inside* the deployment unit — internal services, handlers, domain logic. If it's inside the surface, it runs for real.

#### In-Process Substitute (Preferred)

Two forms, same tier — both run in-process and exercise the real wire protocol, so either is preferred over testcontainers or hand-written fakes.

**Embedded real service (highest fidelity).** When the dependent service is in the same language and ships an embedded constructor (by convention `NewEmbedded()` or similar), the real service can be booted in-process with minimal wiring. Consumers call it directly from their tests:

```go
func TestOrderWithPayments(t *testing.T) {
    // Given: the payments service running embedded — real code, real handlers
    payments := paymentssvc.NewEmbedded(paymentssvc.EmbeddedOptions{
        // payments' own external deps get substituted here, recursively
    })
    defer payments.Shutdown()

    // Given: the order service wired to the embedded payments service
    server := api.NewServer(api.ServerOptions{
        PaymentsURL: payments.URL(),
    })
    go server.Start("localhost:0")
    defer server.Shutdown()

    // When/Then: exercise through the Order surface — real payments code runs
}
```

This is higher fidelity than any fake: the *real* payments code runs, using its real business logic, real HTTP handlers, and real wire protocol. You only substitute the payments service's own external dependencies (recursively applying the same rules).

**Services consumed by other services should ship an embedded constructor.** This is the provider-side obligation: making a service easy to boot in-process is what lets its consumers write high-fidelity tests against it. An in-memory store (see the Databases section below) is often a prerequisite for a good embedded mode.

**Published in-process fake library.** When no embedded version of the dependent service is available (or the service is third-party), check whether a published in-process fake library exists. For example, [gofakes3](https://github.com/johannesboyne/gofakes3) is an in-process S3-compatible server:

```go
func TestImageUpload(t *testing.T) {
    // Given: an in-process S3 fake
    backend := s3mem.New()
    s3srv := httptest.NewServer(gofakes3.New(backend).Server())
    defer s3srv.Close()

    // Given: a running server wired to the fake
    server := api.NewServer(api.ServerOptions{
        S3Endpoint: s3srv.URL,
        S3Bucket:   "images",
    })
    go server.Start("localhost:0")
    defer server.Shutdown()

    // When: uploading an image through the HTTP surface
    resp, err := http.Post(server.URL()+"/images", "image/png", bytes.NewReader(pngBytes))
    require.NoError(t, err)
    assert.Equal(t, http.StatusCreated, resp.StatusCode)

    // Then: the object exists in S3 — verified via the real S3 protocol
    obj, err := newS3Client(s3srv.URL).GetObject(ctx, &s3.GetObjectInput{
        Bucket: aws.String("images"),
        Key:    aws.String("expected-key"),
    })
    require.NoError(t, err)
    require.NotNil(t, obj)
}
```

Look for equivalent libraries for the service you need to substitute (Kafka, Redis, SMTP, etc.). When one exists in your language, use it — you get real protocol behavior without paying for a container.

#### Testcontainers (When No In-Process Library Exists)

When no in-process fake exists but the service's authors publish a fake as a container, use testcontainers. The test shape is the same as the in-process version — swap the fake's construction for a container and wire its endpoint to the server:

```go
container, err := testcontainers.GenericContainer(ctx, testcontainers.GenericContainerRequest{
    ContainerRequest: testcontainers.ContainerRequest{
        Image:        "sculley/fake-s3",
        ExposedPorts: []string{"4569/tcp"},
        WaitingFor:   wait.ForListeningPort("4569/tcp"),
    },
    Started: true,
})
require.NoError(t, err)
defer container.Terminate(ctx)

endpoint, _ := container.Endpoint(ctx, "http")
server := api.NewServer(api.ServerOptions{S3Endpoint: endpoint})
// ...exercise the surface and assert the downstream S3 result as before.
```

Testcontainers is slower than in-process but still runs the real protocol over a real network connection. Reach for it only when an in-process fake doesn't exist.

#### Hand-Written Fake (Last Resort)

Only when no published substitute exists should you write your own. A hand-written fake skips the wire protocol entirely — no TCP, no serialization, no client-library code path. You're testing your handler against your mental model, not against real service behavior. That's why it's the last resort.

Keep it simple — a recorder that captures what was sent:

```go
type FakeEventBroker struct {
    mu     sync.Mutex
    events []Event
}

func (f *FakeEventBroker) Publish(event Event) error {
    f.mu.Lock()
    defer f.mu.Unlock()
    f.events = append(f.events, event)
    return nil
}

func (f *FakeEventBroker) Events() []Event {
    f.mu.Lock()
    defer f.mu.Unlock()
    return append([]Event{}, f.events...)
}
```

Inject the fake through the options struct and assert on what it captured:

```go
func TestOrderEmitsEvent(t *testing.T) {
    // Given: a running server with a fake event broker
    fakeBroker := &FakeEventBroker{}
    server := api.NewServer(api.ServerOptions{
        EventBroker: fakeBroker,
    })
    go server.Start("localhost:0")
    defer server.Shutdown()

    // When: submitting an order via HTTP
    resp, err := http.Post(server.URL()+"/orders", "application/json",
        strings.NewReader(`{"item":"widget","qty":5}`))
    require.NoError(t, err)
    assert.Equal(t, http.StatusAccepted, resp.StatusCode)

    // Then: an order event was emitted to the broker
    require.Eventually(t, func() bool {
        return len(fakeBroker.Events()) > 0
    }, time.Second, 10*time.Millisecond)

    event := fakeBroker.Events()[0]
    assert.Equal(t, "order.created", event.Type)
    assert.Equal(t, "widget", event.Payload["item"])
    assert.Equal(t, 5, event.Payload["qty"])
}
```

#### Kotlin/Micronaut Equivalent

The same hierarchy applies on the JVM: prefer a real in-process fake (many services have JVM-embedded versions), then testcontainers, then a hand-written fake as last resort. Substitute at the DI boundary with `@MockBean` or `@Replaces`:

```kotlin
@MicronautTest
class OrderControllerTest {
    @Inject lateinit var client: HttpClient
    @Inject lateinit var fakeBroker: FakeEventBroker

    @Test fun `should emit order event when order is submitted`() {
        val response = client.toBlocking().exchange(
            HttpRequest.POST("/orders", mapOf("item" to "widget", "qty" to 5)),
            Map::class.java)
        assertEquals(HttpStatus.ACCEPTED, response.status)

        await().atMost(Duration.ofSeconds(1)).untilAsserted {
            val events = fakeBroker.events()
            assertEquals(1, events.size)
            assertEquals("order.created", events[0].type)
        }
    }

    @MockBean(EventBroker::class) fun eventBroker(): EventBroker = FakeEventBroker()
}
```

`@MockBean` here replaces an *external* dependency — the event broker is a system boundary. The full application context still boots, the request still goes through HTTP, and all internal services run for real. `await().atMost()` (Awaitility) is the Kotlin equivalent of Go's `require.Eventually`.

**Never use `@MockBean` for internal components.** `@MockBean(UserService::class)` or `@MockBean(OrderRepository::class)` means you are testing implementation, not behavior. Either `@MockBean` or `@Replaces` works — the rule is the same: only substitute *external* boundaries.

### Controlling Time

Time is a cross-cutting concern, not an external dependency — but it still needs to be controlled by tests. Routing time reads through an injected clock does not violate "never substitute internal components": a clock is effectively a global dependency, and making it injectable is what makes time-dependent behavior (retries, expiries, scheduled flushes) testable without sleeping.

For Go, use a package like [kapetan-io/tackle/clock](https://github.com/kapetan-io/tackle/tree/main/clock). Create a per-test provider with `clock.NewProvider()`, freeze it, and inject it into the service through its options struct. Production code reads time through the injected provider's `Now()`, `After()`, `NewTimer()`, etc. — so freezes and advances propagate to every code path that uses it:

```go
func TestRetryAfterBackoff(t *testing.T) {
    // Given: a frozen clock provider to inject into the service
    clk := clock.NewProvider()
    clk.Freeze(time.Now())
    defer clk.UnFreeze()

    // Given: a running server with the clock injected
    server := api.NewServer(api.ServerOptions{Clock: clk})
    go server.Start("localhost:0")
    defer server.Shutdown()

    // When: kicking off an operation that retries after 30s
    resp, err := http.Post(server.URL()+"/jobs", "application/json", strings.NewReader(`{}`))
    require.NoError(t, err)
    assert.Equal(t, http.StatusAccepted, resp.StatusCode)

    // Then: advancing past the backoff fires the retry
    clk.Advance(31 * time.Second)
    require.Eventually(t, func() bool {
        return jobStatus(server) == "retried"
    }, time.Second, 10*time.Millisecond)
}
```

**Pitfall: inject consistently, don't capture.** Every time read in the service must go through the injected provider. If a code path bypasses it (calls `time.Now()` directly, or captures `clock.Realtime()` at construction), those paths won't see the freeze — tests will either flake or silently rely on wall-clock time. Common gotcha; expect to hit it once before the pattern sticks.

Kotlin/JVM has similar options: `java.time.Clock` injected via DI (Micronaut can bind a mutable test `Clock` in a test context), or `TestCoroutineScheduler` for coroutine-based timing. The principle is the same — route all time reads through an injectable source, and inject a controllable version in tests.

### Fault Injection at the Boundary

Some behaviors only show up under failure — retries, circuit breakers, fallback paths, crash recovery. The happy path can't exercise them, and reaching inside to make a specific function return an error couples the test to implementation.

**Inject faults at the dependency boundary, not inside the system.** The system under test should see a real network error, a real timeout, a real disconnect — indistinguishable from what would happen in production.

- **Real dependencies via testcontainers:** kill or pause the container, or put [toxiproxy](https://github.com/Shopify/toxiproxy) between the app and the dependency to inject latency, resets, or partitions. The app still uses its real client, real retry logic, real timeouts.
- **In-process or hand-written fakes:** give them a small "next call fails with X" hook. The fault enters through the same wire protocol the app would see in production.

Assert on observable recovery through the surface — the request eventually succeeds, the circuit-breaker state is reported via a status endpoint, the retry count is visible in `Stats()`. If the recovery isn't observable anywhere, either expose it (next section) or the behavior isn't important enough to test.

Never inject a fault by mocking an internal function to return an error. That tests whether your error handling compiles, not whether it works.

### Last Resort: Expose Observability APIs

Some behaviors have no observable downstream effect through the public interface. These are internal system operations users depend on implicitly but can't query directly — periodic disk flushes, WAL writes, cache eviction, compaction.

Consider a database that syncs data pages to disk at a specific interval and writes WAL entries. You can verify the data is in the database, but you can't assert *when* the sync occurred or *that* WAL entries were written through normal queries.

In this situation, expose a statistics API:

```go
type Stats struct {
    WALWriteCount     int64
    WALLastWriteTime  time.Time
    DirtyPages        int64
    PagesFlushedToWAL int64
    PagesFlushedToDB  int64
}

func (db *DB) Stats() Stats {
    return db.stats.snapshot()
}
```

```go
func TestWALPeriodicWrite(t *testing.T) {
    db := NewDB(DBOptions{WALFlushInterval: 100 * time.Millisecond})
    defer db.Close()

    require.NoError(t, db.Insert("key", "value"))

    require.Eventually(t, func() bool {
        s := db.Stats()
        return s.WALWriteCount > 0 && s.DirtyPages == 0
    }, time.Second, 10*time.Millisecond)
    assert.Greater(t, db.Stats().PagesFlushedToWAL, int64(0))
}
```

`Stats()` isn't test-only code — it's useful in production for monitoring and diagnostics. The test uses the same observability a production operator would.

### Decision Tree

```
Can I assert the result through the public interface?
├─ Yes → Poll, capture, or query the downstream effect
│        • Query an API endpoint for the result
│        • Poll a fake external service (S3, Kafka, SMTP) for captured output
│        • Read events from a fake message broker
└─ No → Is this behavior important to correctness?
         ├─ No → Don't test it
         └─ Yes → Expose an observability API (stats, metrics, status)
                  that serves both tests and production users
```

## Databases Are a Special Case

Databases sit outside your surface — they are external dependencies — but they are the most tightly coupled external dependency your system has. Query semantics, transaction boundaries, isolation levels, constraint behaviors, and migration correctness all live in the database. Hand-written database fakes and in-memory substitutes almost always diverge from the real database in ways that matter (transaction and rollback semantics, null ordering, unique-constraint timing, and row-level locking are common traps).

**The default: use the real database.** Start it with testcontainers or a local instance wired for tests. This is the only way to exercise the real driver, the real wire protocol, the real query planner, and the real constraint system. It's also the only way to catch migration bugs — so **use your real migrations in tests too**, never inline schema creation. The migrations themselves are part of what the test validates.

### The Store/Repository Pattern Lets You Opt Into Speed

Some tests don't care about database behavior — they exercise business logic and only use the database as passive state. For those tests, a real database is unnecessary overhead. To opt into a faster path without losing the real-database safety net, structure data access behind a store interface (sometimes called a repository):

```go
type OrderStore interface {
    Save(ctx context.Context, order Order) error
    Get(ctx context.Context, id string) (Order, error)
    ListPending(ctx context.Context) ([]Order, error)
}

type PostgresOrderStore struct { /* real impl */ }
type InMemoryOrderStore struct { /* map-backed impl */ }
```

Tests inject whichever store fits the scenario:

- **Tests exercising database-adjacent behavior** (complex queries, constraints, transactions, migrations) — `PostgresOrderStore` wired via testcontainers.
- **Tests exercising business logic that happens to persist state** — `InMemoryOrderStore` for speed.

Both paths still enter through the surface. The store choice is an injected dependency, not a shortcut around the surface. Never substitute the store with a mock that asserts `verify { store.save(any()) }` — that's testing implementation. The in-memory store is a *real* implementation: it persists and returns data. Tests assert on observable results through the surface, not on which store methods were called.

### The Cost of Building an In-Memory Store

Building an in-memory store is not a free optimization. It introduces a second implementation of your data layer that must remain behaviorally equivalent to the real database — and the two *will* drift. Every new feature that adds a query or a constraint adds surface area where drift can happen silently.

**If you build one, you must test for parity.** Two valid models:

- **Option 1 — Full suite against both implementations.** Every store-touching test runs twice (real DB + in-memory). Highest cost, highest safety. Right when the in-memory store is *also a deployment target* (embedded/e2e mode) — it's production code and deserves full validation.
- **Option 2 — Dedicated store-contract suite.** A focused suite validates both implementations behave identically for the operations the app uses; feature tests pick one store (real DB by default, in-memory when speed matters) and trust the contract suite to catch drift. Lower cost, reasonable safety. Right when the in-memory store exists *only to speed up tests* — doubling the full suite rarely pays for itself.

Pick based on whether the in-memory path is a product feature or a test optimization.

### The Embedded-Mode Advantage

A well-designed in-memory store gives you more than test speed. It lets the service run in "embedded" or "integration" mode — no database, no network hops — which is valuable for:

- End-to-end tests that exercise multiple services together in a controlled environment.
- Limited deployment environments where running a full database stack isn't practical.
- Local development loops where iterating against a real database would slow things down.

If your service needs any of these, the in-memory store pays for itself beyond tests, and that's often what tips the decision toward building one — and toward Option 1 parity testing.

## Language-Specific Rules

### Go

**Tests MUST be in `package xxx_test`** — because this prevents the test from accessing unexported identifiers, which forces it to enter through the public interface. If your test won't compile in `package xxx_test`, that's the signal you're trying to test internals. This applies equally to internal library boundaries — packages within the same codebase that expose a complete domain API are tested as libraries, from `package xxx_test`, never from inside.

### Kotlin/Micronaut

These rules apply when the project under test is a **Micronaut application** (HTTP service, gRPC service, etc.). For a Kotlin **library**, the surface is its exported public functions — call them directly from tests as a consumer would; `@MicronautTest` does not apply.

**Micronaut-application tests MUST use `@MicronautTest`** — because this boots the full application context with real dependency injection. If you're instantiating classes with `val service = UserService(mockRepo)`, you've bypassed the surface.

**`@MockBean` and `@Replaces` MUST only substitute external boundaries** — because replacing internal components means the test no longer exercises the real code path. If the bean you're replacing lives inside your application, the test is coupled to implementation.

## How Surface Testing Relates to Integration Testing

They overlap but differ in intent. **Integration testing** asks "do these components work together correctly?" — focus on the seams (Service A↔B, schema↔ORM). **Surface testing** asks "does the system behave correctly when used as intended?" — focus on observable behavior from the outside.

Surface tests boot the full application, so internal components are integrating — but integration is a side effect, not the goal. Surface tests also explicitly fake external boundaries to stay fast, deterministic, and focused on *this* system's behavior; integration tests typically wire real things together. Complementary, not interchangeable.

**Internal library boundaries** sit at the intersection of both: a domain-complete package within the codebase defines its own surface and warrants its own surface tests, independent of the systems that consume it. When integration tests wire two components together, an internal library boundary is where you draw the line — it is a first-class surface, not an internal seam to cut through.

## Key Principles

1. **Test behavior through the surface** (including internal library boundaries, which define their own surface): Tests act as end-users and verify what the system does, not how. If a test needs internal access, the design is wrong — fix the design (expose observability), not the test strategy. Only behavior changes should break tests.
2. **Preserve the production stack**: A test's value is proportional to how much of the production code path it exercises — real TCP, real HTTP clients, real serialization, real migrations. Fidelity is the metric, not speed.
3. **Real fakes at external boundaries only**: Substitute externals with real fakes (in-process libraries or testcontainers) that exercise the real protocol. Hand-written fakes are a last resort. Never substitute internal components.
4. **Real database by default**: Use the real database with real migrations. An in-memory store is a deliberate, parity-tested opt-out — not a shortcut.
5. **Dependency injection via options**: Use options structs (Go) or DI context (Micronaut) to inject testable dependencies; the full application boots and all internal components run for real.
