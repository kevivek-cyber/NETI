/**
 * Client-side cryptographic hashing for response chains.
 * Implements INTEGRITY.md §8 and matches backend/app/ledger/canonical.py.
 */

class NonCanonical extends Error {
  constructor(message: string) {
    super(message);
    this.name = "NonCanonical";
  }
}

function rejectFloats(obj: any, path: string = "$") {
  if (typeof obj === "number" && !Number.isInteger(obj)) {
    throw new NonCanonical(`float at ${path}; use a fixed-precision string`);
  }
  if (obj !== null && typeof obj === "object") {
    if (Array.isArray(obj)) {
      obj.forEach((value, index) => rejectFloats(value, `${path}[${index}]`));
    } else {
      for (const key of Object.keys(obj)) {
        if (typeof key !== "string") {
          throw new NonCanonical(`non-string key at ${path}`);
        }
        rejectFloats(obj[key], `${path}.${key}`);
      }
    }
  }
}

/**
 * Serialise to the one byte form that gets hashed.
 * Approximates RFC 8785 (JCS): sorted keys, no insignificant whitespace.
 */
export function canonicalBytes(obj: any): Uint8Array {
  rejectFloats(obj);
  
  // Recursively sort object keys
  const sortKeys = (o: any): any => {
    if (o === null || typeof o !== "object") {
      return o;
    }
    if (Array.isArray(o)) {
      return o.map(sortKeys);
    }
    const sorted: Record<string, any> = {};
    Object.keys(o)
      .sort()
      .forEach((key) => {
        sorted[key] = sortKeys(o[key]);
      });
    return sorted;
  };

  const sortedObj = sortKeys(obj);
  const jsonStr = JSON.stringify(sortedObj);
  return new TextEncoder().encode(jsonStr);
}

function hexToBytes(hex: string): Uint8Array {
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < bytes.length; i++) {
    bytes[i] = parseInt(hex.substring(i * 2, i * 2 + 2), 16);
  }
  return bytes;
}

function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

const DOMAIN_RESPONSE = new Uint8Array([0x03]);

async function sha256(data: Uint8Array): Promise<Uint8Array> {
  const hashBuffer = await crypto.subtle.digest("SHA-256", data as unknown as BufferSource);
  return new Uint8Array(hashBuffer);
}

/**
 * r_0 = SHA-256(0x03 || paper_hash)
 */
export async function hashResponseInitial(paperHashHex: string): Promise<string> {
  const paperHashBytes = hexToBytes(paperHashHex);
  const data = new Uint8Array(DOMAIN_RESPONSE.length + paperHashBytes.length);
  data.set(DOMAIN_RESPONSE);
  data.set(paperHashBytes, DOMAIN_RESPONSE.length);
  
  const hash = await sha256(data);
  return bytesToHex(hash);
}

/**
 * r_i = SHA-256(0x03 || r_{i-1} || canonical_bytes(event_i))
 */
export async function hashResponseStep(prevHashHex: string, event: any): Promise<string> {
  const prevHashBytes = hexToBytes(prevHashHex);
  const eventBytes = canonicalBytes(event);
  
  const data = new Uint8Array(DOMAIN_RESPONSE.length + prevHashBytes.length + eventBytes.length);
  data.set(DOMAIN_RESPONSE);
  data.set(prevHashBytes, DOMAIN_RESPONSE.length);
  data.set(eventBytes, DOMAIN_RESPONSE.length + prevHashBytes.length);
  
  const hash = await sha256(data);
  return bytesToHex(hash);
}
