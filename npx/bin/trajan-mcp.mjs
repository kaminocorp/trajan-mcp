#!/usr/bin/env node

/**
 * npx wrapper for trajan-mcp.
 *
 * Tries to run the Python MCP server in order of preference:
 *   1. uvx trajan-mcp  (zero-install, fastest)
 *   2. trajan-mcp      (pip-installed on PATH)
 *   3. pipx run trajan-mcp
 *
 * All env vars (TRAJAN_API_KEY, TRAJAN_API_URL) are forwarded automatically.
 */

import { spawn, execFileSync } from "node:child_process";

function commandExists(cmd) {
  try {
    execFileSync("which", [cmd], { stdio: "ignore" });
    return true;
  } catch {
    return false;
  }
}

function run(cmd, args) {
  const child = spawn(cmd, args, {
    stdio: "inherit",
    env: process.env,
  });
  child.on("exit", (code) => process.exit(code ?? 1));
  child.on("error", () => {
    process.stderr.write(`Failed to start: ${cmd} ${args.join(" ")}\n`);
    process.exit(1);
  });
}

if (commandExists("uvx")) {
  run("uvx", ["trajan-mcp"]);
} else if (commandExists("trajan-mcp")) {
  run("trajan-mcp", []);
} else if (commandExists("pipx")) {
  run("pipx", ["run", "trajan-mcp"]);
} else {
  process.stderr.write(
    "Error: trajan-mcp requires Python. Install one of:\n" +
      "  - uv:   curl -LsSf https://astral.sh/uv/install.sh | sh\n" +
      "  - pip:  pip install trajan-mcp\n" +
      "  - pipx: pipx install trajan-mcp\n"
  );
  process.exit(1);
}
