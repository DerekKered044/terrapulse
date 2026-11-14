// MapLibre runs tile work in a web worker loaded by URL. Bundlers do not always
// emit that file at a resolvable path (it broke under a GitHub Pages sub-path),
// so copy it into public/ and point MapLibre at it with setWorkerUrl().
import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
mkdirSync(join(root, "public"), { recursive: true });
copyFileSync(
  join(root, "node_modules", "maplibre-gl", "dist", "maplibre-gl-worker.mjs"),
  join(root, "public", "maplibre-gl-worker.mjs"),
);
