import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const packageDirectory = resolve(repositoryRoot, "node_modules", "markdownlint-cli");
const packageManifestPath = resolve(packageDirectory, "package.json");

/**
 * Run a child process and report launch failures with a non-zero status.
 *
 * @param {string} command Executable to run.
 * @param {string[]} args Arguments passed without shell interpolation.
 * @returns {{ status: number, stdout: string, stderr: string }} Captured result.
 */
function run(command, args) {
  const result = spawnSync(command, args, {
    cwd: repositoryRoot,
    encoding: "utf8",
    maxBuffer: 10 * 1024 * 1024,
  });

  if (result.error) {
    process.stderr.write(`Unable to run ${command}: ${result.error.message}\n`);
    return { status: 1, stdout: result.stdout ?? "", stderr: result.stderr ?? "" };
  }

  return {
    status: result.status ?? 1,
    stdout: result.stdout ?? "",
    stderr: result.stderr ?? "",
  };
}

/**
 * Return tracked Markdown paths from the Git index.
 *
 * @returns {string[] | null} Markdown paths, or null if Git discovery failed.
 */
function discoverMarkdownFiles() {
  const result = run("git", ["ls-files", "-z"]);
  if (result.status !== 0) {
    process.stderr.write(result.stderr || "Git could not list tracked files.\n");
    return null;
  }

  return result.stdout
    .split("\0")
    .filter((filePath) => /\.md$/i.test(filePath));
}

/**
 * Split paths into bounded batches for the markdownlint command line.
 *
 * @param {string[]} files Tracked Markdown paths.
 * @returns {string[][]} Batches limited by count and argument size.
 */
function createBatches(files) {
  const batches = [];
  let batch = [];
  let batchBytes = 0;

  for (const filePath of files) {
    const fileBytes = Buffer.byteLength(filePath) + 1;
    if (batch.length > 0 && (batch.length >= 100 || batchBytes + fileBytes > 24 * 1024)) {
      batches.push(batch);
      batch = [];
      batchBytes = 0;
    }
    batch.push(filePath);
    batchBytes += fileBytes;
  }

  if (batch.length > 0) {
    batches.push(batch);
  }
  return batches;
}

/**
 * Lint all tracked Markdown files and propagate every lint failure.
 *
 * @returns {number} Process exit code.
 */
function main() {
  let markdownlintCommand;
  try {
    const manifest = JSON.parse(readFileSync(packageManifestPath, "utf8"));
    const binary = typeof manifest.bin === "string"
      ? manifest.bin
      : manifest.bin?.markdownlint;
    if (!binary) {
      throw new Error("the markdownlint-cli package does not declare its markdownlint binary");
    }
    markdownlintCommand = resolve(packageDirectory, binary);
  } catch (error) {
    process.stderr.write(`Unable to locate the local markdownlint-cli binary: ${error.message}\n`);
    return 1;
  }

  const files = discoverMarkdownFiles();
  if (files === null) {
    return 1;
  }
  if (files.length === 0) {
    process.stdout.write("No tracked Markdown files found.\n");
    return 0;
  }

  let failed = false;
  for (const batch of createBatches(files)) {
    const result = run(process.execPath, [markdownlintCommand, "--", ...batch]);
    if (result.stdout) {
      process.stdout.write(result.stdout);
    }
    if (result.stderr) {
      process.stderr.write(result.stderr);
    }
    if (result.status !== 0) {
      failed = true;
    }
  }

  if (!failed) {
    process.stdout.write(`Validated ${files.length} tracked Markdown files.\n`);
    return 0;
  }
  return 1;
}

process.exitCode = main();
