# Campus for Linux

Campus on Linux could be two different things, and neither is built yet:

- a desktop client with the board and the island, and
- Campus running headless on a Linux server, with agents working on code checked out there.

They serve different people, and the second may matter more. [PRD.md](PRD.md) treats them separately.

Like every Campus client, it will only show what the Campus API decides. The API contract is in [docs/api/openapi.yaml](docs/api/openapi.yaml), and the live clients, [campus-macos](https://github.com/yuric/campus-macos) and [campus-cli](https://github.com/yuric/campus-cli), show how it works in practice.

Ideas and design discussion are welcome as issues. Licensed under Apache-2.0, see [LICENSE](LICENSE).
