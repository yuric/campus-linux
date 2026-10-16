# Campus for Linux

The planned Linux desktop client for Campus, with macOS feature parity and a local
execution service for coding agents and the same visual identity as the Mac app,
as closely as practical with Linux integration. It will control local and remote agents through
the Campus API. Ubuntu is the first verification target; broad Linux compatibility
is a design goal with an explicit tested support matrix.

**Status: specification decided; application and execution service not implemented.**
Tauri with a React board, Rust for the host and executor, Secret Service for secrets, deb
and AppImage with signed in-app updates, one production channel. The decisions and their
trade-offs are in [PRD.md section 4](PRD.md#4-architecture-and-decisions).

- [Product requirements and delivery gates](PRD.md)
- [Feature PRD directory](TODO/README.md)
- [Architecture](ARCHITECTURE.md)
- [Contributing](CONTRIBUTING.md)
- [API snapshot](docs/api/openapi.yaml), imported from `yuric/campus-server`;
  current provenance must be verified before implementation

The API decides product behavior; this client renders it. The reference implementation
and Island renderer live in [campus-macos](https://github.com/yuric/campus-macos).
The retired web and CLI clients are not implementation dependencies.

Licensed under Apache-2.0. See [LICENSE](LICENSE).
