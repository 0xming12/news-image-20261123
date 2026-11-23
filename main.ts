// "The World Today" — one-image summary of Monday 23 November 2026.
// Node 22, standard library only. The image is rendered by the build
// script and shipped beside this file; the program copies it to the
// output directory the grader provides, and refuses to write anything
// that is not a whole PNG or JPEG inside the 1 MiB limit.
//
// Outside the grader's container, MAKEFUN_OUTPUT_DIR stands in for
// /output:
//   mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const MAX_BYTES = 1_048_576; // 1 MiB
const PNG_MAGIC = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
const JPEG_MAGIC = Buffer.from([0xff, 0xd8, 0xff]);

function checkImage(bytes: Buffer): void {
  if (bytes.length === 0 || bytes.length > MAX_BYTES) {
    throw new Error(`Image is ${bytes.length} bytes; the limit is ${MAX_BYTES}`);
  }
  const isPng = bytes.subarray(0, 8).equals(PNG_MAGIC);
  const isJpeg = bytes.subarray(0, 3).equals(JPEG_MAGIC);
  if (!isPng && !isJpeg) {
    throw new Error("Source image is neither a PNG nor a JPEG");
  }
}

function main(): void {
  const rootDir = path.dirname(fileURLToPath(import.meta.url));
  const sourcePath = path.join(rootDir, "entry.png");
  const outputDir = process.env.MAKEFUN_OUTPUT_DIR || "/output";
  const destPath = path.join(outputDir, "entry.png");

  const imageBytes = fs.readFileSync(sourcePath);
  checkImage(imageBytes);

  fs.mkdirSync(outputDir, { recursive: true });
  fs.writeFileSync(destPath, imageBytes);

  // Read the copy back and prove it is byte-for-byte the source image:
  // the two grading runs must write identical bytes.
  const written = fs.readFileSync(destPath);
  if (!written.equals(imageBytes)) {
    throw new Error("Written image differs from the source image");
  }
}

main();
