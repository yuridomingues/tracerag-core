import { lookup } from "node:dns/promises";
import https from "node:https";
import { isIP } from "node:net";

const MAX_RESPONSE_BYTES = 1_048_576;

function isPrivateIpv4(ip: string): boolean {
  const parts = ip.split(".").map(Number);
  if (parts.length !== 4 || parts.some((part) => !Number.isInteger(part))) {
    return true;
  }

  const [a, b] = parts;
  return (
    a === 0 ||
    a === 10 ||
    a === 127 ||
    (a === 100 && b >= 64 && b <= 127) ||
    (a === 169 && b === 254) ||
    (a === 172 && b >= 16 && b <= 31) ||
    (a === 192 && b === 168) ||
    (a === 198 && (b === 18 || b === 19)) ||
    a >= 224
  );
}

function isPrivateIpv6(ip: string): boolean {
  const normalized = ip.toLowerCase();

  if (normalized.startsWith("::ffff:")) {
    const mapped = normalized.slice("::ffff:".length);
    return isPrivateIpv4(mapped);
  }

  return (
    normalized === "::" ||
    normalized === "::1" ||
    normalized.startsWith("fc") ||
    normalized.startsWith("fd") ||
    normalized.startsWith("fe8") ||
    normalized.startsWith("fe9") ||
    normalized.startsWith("fea") ||
    normalized.startsWith("feb")
  );
}

function isPrivateAddress(address: string): boolean {
  const family = isIP(address);
  if (family === 4) return isPrivateIpv4(address);
  if (family === 6) return isPrivateIpv6(address);
  return true;
}

async function resolveSafeAddress(hostname: string) {
  if (hostname.toLowerCase() === "localhost") {
    throw new Error("Localhost endpoints are not allowed.");
  }

  if (isIP(hostname)) {
    if (isPrivateAddress(hostname)) {
      throw new Error("Private or local IP endpoints are not allowed.");
    }
    return { address: hostname, family: isIP(hostname) as 4 | 6 };
  }

  const addresses = await lookup(hostname, { all: true, verbatim: true });
  if (!addresses.length) {
    throw new Error("Endpoint hostname did not resolve.");
  }

  if (addresses.some((item) => isPrivateAddress(item.address))) {
    throw new Error("Endpoint resolves to a private or local network.");
  }

  return addresses[0];
}

export async function postJsonSafely(
  endpoint: string,
  payload: Record<string, unknown>,
  headers: Record<string, string>,
  timeoutMs = 8_000,
): Promise<{ status: number; body: unknown; latencyMs: number }> {
  const url = new URL(endpoint);

  if (url.protocol !== "https:") {
    throw new Error("Only HTTPS endpoints are allowed.");
  }

  if (url.username || url.password) {
    throw new Error("Credentials in endpoint URLs are not allowed.");
  }

  const resolved = await resolveSafeAddress(url.hostname);
  const startedAt = performance.now();
  const body = JSON.stringify(payload);

  return await new Promise((resolve, reject) => {
    const request = https.request(
      {
        protocol: "https:",
        hostname: url.hostname,
        port: url.port ? Number(url.port) : 443,
        path: `${url.pathname}${url.search}`,
        method: "POST",
        servername: url.hostname,
        headers: {
          ...headers,
          "content-length": Buffer.byteLength(body).toString(),
        },
        lookup: (_hostname, _options, callback) => {
          callback(null, resolved.address, resolved.family);
        },
      },
      (response) => {
        const chunks: Buffer[] = [];
        let size = 0;

        response.on("data", (chunk: Buffer) => {
          size += chunk.length;
          if (size > MAX_RESPONSE_BYTES) {
            request.destroy(new Error("Endpoint response exceeded 1 MiB."));
            return;
          }
          chunks.push(chunk);
        });

        response.on("end", () => {
          const latencyMs = Math.round(performance.now() - startedAt);
          const raw = Buffer.concat(chunks).toString("utf8");

          try {
            resolve({
              status: response.statusCode ?? 0,
              body: raw ? JSON.parse(raw) : null,
              latencyMs,
            });
          } catch {
            reject(new Error("Endpoint did not return valid JSON."));
          }
        });
      },
    );

    request.setTimeout(timeoutMs, () => {
      request.destroy(new Error("Endpoint request timed out."));
    });
    request.on("error", reject);
    request.end(body);
  });
}
