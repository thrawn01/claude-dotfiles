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

**Every test must interact with the system the same way its end users would.** The surface varies by project type:

- **HTTP APIs**: Test by making HTTP requests to a running server
- **CLIs**: Test by calling the entry point function with arguments and capturing output
- **Libraries**: Test by calling exported/public functions

Never call internal/private functions directly in tests. If you can't observe a behavior through the surface, that's a design signal — fix the design, not the test strategy.

## Finding the Surface

Before writing tests, identify the public interface. Work through these questions in order:

### Is this an application with an HTTP/gRPC API?
The surface is the API endpoints. Boot the full application and make real HTTP requests. Do not instantiate controllers, handlers, or services directly.

### Is this a CLI application?
The surface is the `Run()` function. Call it with arguments and capture output. Do not call subcommand handlers or internal functions directly.

### Is this a library consumed by other packages?
The surface is the exported/public functions. Call them the way a consumer would. Do not call unexported/private functions.

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
package cmd_test

import (
    "bytes"
    "testing"
    "yourproject/cmd"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

func TestSubCommand(t *testing.T) {
    // Given: captured output
    var stdout bytes.Buffer

    // When: running the subcommand
    exitCode := cmd.Run([]string{"sub-command", "-f", "filename.ext"}, cmd.RunOptions{
        Stdout: &stdout,
    })

    // Then: it succeeds with expected output
    require.Equal(t, 0, exitCode)
    assert.Contains(t, stdout.String(), "expected output")
}
```

### HTTP Services (Go)

Start a real server in tests and make real HTTP requests:

```go
package api_test

import (
    "net/http"
    "strings"
    "testing"
    "yourproject/api"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

func TestCreateUser(t *testing.T) {
    // Given: a running server
    server := api.NewServer(api.ServerOptions{
        // inject real or test dependencies here
    })
    go server.Start("localhost:0")
    defer server.Shutdown()

    // When: creating a user via HTTP
    resp, err := http.Post(
        server.URL()+"/users",
        "application/json",
        strings.NewReader(`{"name":"Alice"}`),
    )
    require.NoError(t, err)
    defer resp.Body.Close()

    // Then: the response confirms creation
    assert.Equal(t, http.StatusCreated, resp.StatusCode)
}
```

### HTTP Services (Kotlin/Micronaut)

**Wrong approach** — testing a service in isolation:

```kotlin
// DON'T DO THIS
class UserServiceTest {
    private val repository = mockk<UserRepository>()
    private val service = UserService(repository)

    @Test
    fun `should create user`() {
        every { repository.save(any()) } returns User("Alice")

        val result = service.createUser("Alice")

        assertEquals("Alice", result.name)
        verify { repository.save(any()) }
    }
}
```

This test calls the service directly, mocks its dependencies, and verifies internal method calls. It will break on any refactoring of `UserService` even if the API behavior is unchanged.

**Right approach** — boot the full application and go through HTTP:

```kotlin
@MicronautTest
class UserControllerTest {

    @Inject
    lateinit var client: HttpClient

    @Test
    fun `should create user`() {
        // When: creating a user via HTTP
        val response = client.toBlocking().exchange(
            HttpRequest.POST("/users", mapOf("name" to "Alice")),
            Map::class.java
        )

        // Then: the response confirms creation
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

### Using Fakes to Capture Output at External Boundaries

When async behavior produces output to an external system (message broker, object store, email service, payment gateway), replace that external dependency with a fake that captures what was sent to it. The system under test still boots fully and enters through the surface — only the external boundary is replaced.

Fakes are injected through the options struct:

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

The fake is simple — it just records what it received:

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

**Key distinction**: fakes replace *external* dependencies at the system boundary — services your application talks to but doesn't own. Never fake internal components like repositories, services, or handlers. If it's inside the surface, it runs for real.

#### Kotlin/Micronaut Equivalent

```kotlin
@MicronautTest
class OrderControllerTest {

    @Inject
    lateinit var client: HttpClient

    @Inject
    lateinit var fakeBroker: FakeEventBroker

    @Test
    fun `should emit order event when order is submitted`() {
        // When: submitting an order via HTTP
        val response = client.toBlocking().exchange(
            HttpRequest.POST("/orders", mapOf("item" to "widget", "qty" to 5)),
            Map::class.java
        )

        // Then: the request was accepted
        assertEquals(HttpStatus.ACCEPTED, response.status)

        // And: an order event was emitted to the broker
        await().atMost(Duration.ofSeconds(1)).untilAsserted {
            val events = fakeBroker.events()
            assertEquals(1, events.size)
            assertEquals("order.created", events[0].type)
            assertEquals("widget", events[0].payload["item"])
            assertEquals(5, events[0].payload["qty"])
        }
    }

    @MockBean(EventBroker::class)
    fun eventBroker(): EventBroker {
        return FakeEventBroker()
    }
}
```

`@MockBean` here replaces an *external* dependency — the event broker is a system boundary. The full application context still boots, the request still goes through HTTP, and all internal services run for real.

**Never use `@MockBean` for internal components.** If you find yourself writing `@MockBean(UserService::class)` or `@MockBean(OrderRepository::class)`, you are testing implementation, not behavior.

`await().atMost()` (from the Awaitility library) serves the same role as Go's `require.Eventually` — it polls until async behavior becomes observable. This pattern is essential when testing through the surface, because the response returns before the async work completes.

Micronaut provides both `@MockBean` and `@Replaces` for substituting dependencies. Either works — the rule is the same: only substitute *external* boundaries, never internal components.

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
    // Given: a database with a 100ms flush interval
    db := NewDB(DBOptions{
        WALFlushInterval: 100 * time.Millisecond,
    })
    defer db.Close()

    // When: inserting data
    require.NoError(t, db.Insert("key", "value"))

    // Then: the WAL is eventually flushed and pages are clean
    require.Eventually(t, func() bool {
        stats := db.Stats()
        return stats.WALWriteCount > 0 && stats.DirtyPages == 0
    }, time.Second, 10*time.Millisecond)

    stats := db.Stats()
    assert.Greater(t, stats.PagesFlushedToWAL, int64(0))
}
```

This `Stats()` API isn't test-only code. It's useful in production for monitoring and diagnostics. The test simply uses the same observability a production operator would.

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

## Language-Specific Rules

### Go

**Tests MUST be in `package xxx_test`** — because this prevents the test from accessing unexported identifiers, which forces it to enter through the public interface. If your test won't compile in `package xxx_test`, that's the signal you're trying to test internals.

### Kotlin/Micronaut

**Tests MUST use `@MicronautTest`** — because this boots the full application context with real dependency injection. If you're instantiating classes with `val service = UserService(mockRepo)`, you've bypassed the surface.

**`@MockBean` and `@Replaces` MUST only substitute external boundaries** — because replacing internal components means the test no longer exercises the real code path. If the bean you're replacing lives inside your application, the test is coupled to implementation.

## How Surface Testing Relates to Integration Testing

Surface testing and integration testing overlap in practice but differ in intent.

**Integration testing** asks: "do these components work together correctly?" The focus is on the seams between components — does Service A talk to Service B correctly, does the database schema match the ORM mappings.

**Surface testing** asks: "does the system behave correctly when used the way it's intended to be used?" The focus is on observable behavior from the outside. The test enters through the surface and asserts results a real consumer would see.

Surface tests boot the full application, so internal components are integrating — but the integration is a side effect, not the goal. Surface testing also explicitly replaces external boundaries with fakes, which integration testing typically wouldn't, since the point of integration testing is to wire real things together.

If someone asks "isn't this just integration testing?" — the answer is: surface tests verify behavior through the same interface consumers use, and they fake external boundaries to keep tests fast, deterministic, and focused on your system's behavior. Integration tests verify that real components are wired together correctly. They're complementary, not interchangeable.

## Key Principles

1. **Test Behavior, Not Implementation**: Tests verify what the system does, not how it does it
2. **Tests Are End-Users**: If a test needs to call internal functions, the code structure is wrong
3. **Fix the Design, Not the Test Strategy**: If behavior isn't observable through the surface, change the design to make it observable
4. **Fakes at Boundaries Only**: Replace external dependencies with fakes; never fake internal components
5. **Dependency Injection via Options**: Use options structs (Go) or DI context (Micronaut) to inject testable dependencies
6. **Real Execution**: Tests execute real code paths — the full application boots, all internal components run for real
7. **Unchanging Tests**: Tests should survive refactoring, new features, and bug fixes — only behavior changes should break tests
