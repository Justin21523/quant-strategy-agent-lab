import http from "node:http";
import fs from "node:fs/promises";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "..", "dist");
const basePath = "/quant-strategy-agent-lab";
const host = process.env.SHOWCASE_HOST ?? "127.0.0.1";
const port = Number(process.env.SHOWCASE_FRONTEND_PORT ?? "8899");

const contentTypes = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".map": "application/json; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".webm": "video/webm",
  ".webp": "image/webp",
};

function requestPath(url = "/") {
  const pathname = decodeURIComponent(new URL(url, `http://${host}:${port}`).pathname);
  if (pathname === "/" || pathname === basePath || pathname === `${basePath}/`)
    return "/index.html";
  if (!pathname.startsWith(`${basePath}/`)) return "/index.html";
  return pathname.slice(basePath.length) || "/index.html";
}

async function serve(request, response) {
  const relativePath = requestPath(request.url);
  const candidate = path.resolve(root, `.${relativePath}`);
  const safePath = candidate.startsWith(root) ? candidate : path.join(root, "index.html");
  try {
    const stat = await fs.stat(safePath);
    const filePath = stat.isDirectory() ? path.join(safePath, "index.html") : safePath;
    const body = await fs.readFile(filePath);
    response.writeHead(200, {
      "content-type": contentTypes[path.extname(filePath)] ?? "application/octet-stream",
      "cache-control": "no-cache",
    });
    response.end(body);
  } catch {
    const body = await fs.readFile(path.join(root, "index.html"));
    response.writeHead(200, {
      "content-type": "text/html; charset=utf-8",
      "cache-control": "no-cache",
    });
    response.end(body);
  }
}

http.createServer(serve).listen(port, host, () => {
  console.warn(`Serving ${root} at http://${host}:${port}${basePath}/`);
});
