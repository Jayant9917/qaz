import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const allowedCommands = new Set(["build", "dev", "start", "lint", "typecheck", "test"]);
const command = process.argv[2] ?? "build";

if (!allowedCommands.has(command)) {
  console.error(`Unsupported frontend command: ${command}`);
  process.exit(1);
}

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(scriptDir, "..");
const frontendDir = path.join(repoRoot, "frontend");

function toWslPath(winPath) {
  const normalized = path.resolve(winPath);
  const match = normalized.match(/^([A-Za-z]):\\(.*)$/);
  if (!match) {
    throw new Error(`Unsupported Windows path for WSL conversion: ${normalized}`);
  }

  const drive = match[1].toLowerCase();
  const rest = match[2].replace(/\\/g, "/");
  return `/mnt/${drive}/${rest}`;
}

function run(commandLine, args, options = {}) {
  const child = spawn(commandLine, args, {
    stdio: "inherit",
    shell: false,
    windowsVerbatimArguments: process.platform === "win32",
    ...options,
  });

  child.on("error", (error) => {
    console.error(error instanceof Error ? error.message : String(error));
    process.exit(1);
  });

  child.on("exit", (code, signal) => {
    if (signal) {
      process.kill(process.pid, signal);
      return;
    }
    process.exit(code ?? 0);
  });
}

if (process.platform === "win32") {
  const wslFrontendDir = toWslPath(frontendDir);
  const bashCommand = `cd ${wslFrontendDir} && export NEXT_TELEMETRY_DISABLED=1 && pnpm ${command}`;
  run("wsl.exe", ["-d", "Ubuntu", "--", "bash", "-lc", bashCommand]);
} else {
  run("pnpm", ["--dir", frontendDir, command]);
}
