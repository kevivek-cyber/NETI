export enum Domain {
  LEAF = 0x00,
  NODE = 0x01,
  BLOCK = 0x02,
  RESPONSE = 0x03,
  RECEIPT = 0x04,
}

function rejectFloats(obj: any, path = "$"): void {
  if (typeof obj === "number" && !Number.isInteger(obj)) {
    throw new Error(`NonCanonical: float at ${path}`);
  }
  if (Array.isArray(obj)) {
    obj.forEach((val, i) => rejectFloats(val, `${path}[${i}]`));
  } else if (obj !== null && typeof obj === "object") {
    for (const key of Object.keys(obj)) {
      rejectFloats(obj[key], `${path}.${key}`);
    }
  }
}

function sortKeys(obj: any): any {
  if (Array.isArray(obj)) {
    return obj.map(sortKeys);
  } else if (obj !== null && typeof obj === "object") {
    const sorted: Record<string, any> = {};
    for (const key of Object.keys(obj).sort()) {
      sorted[key] = sortKeys(obj[key]);
    }
    return sorted;
  }
  return obj;
}

export function canonicalBytes(obj: any): Uint8Array {
  rejectFloats(obj);
  const sorted = sortKeys(obj);
  const jsonStr = JSON.stringify(sorted);
  return new TextEncoder().encode(jsonStr);
}

export async function digest(domain: Domain, ...parts: Uint8Array[]): Promise<Uint8Array> {
  const totalLength = 1 + parts.reduce((acc, p) => acc + p.length, 0);
  const buffer = new Uint8Array(totalLength);
  
  buffer[0] = domain;
  let offset = 1;
  for (const part of parts) {
    buffer.set(part, offset);
    offset += part.length;
  }
  
  const hashBuffer = await crypto.subtle.digest("SHA-256", buffer);
  return new Uint8Array(hashBuffer);
}

export function hexOf(bytes: Uint8Array): string {
  return Array.from(bytes)
    .map(b => b.toString(16).padStart(2, "0"))
    .join("");
}

export function hexToBytes(hex: string): Uint8Array {
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < hex.length; i += 2) {
    bytes[i / 2] = parseInt(hex.substring(i, i + 2), 16);
  }
  return bytes;
}

export async function hashObject(domain: Domain, obj: any): Promise<Uint8Array> {
  return digest(domain, canonicalBytes(obj));
}

export async function hashLeaf(paper: any): Promise<string> {
  const d = await hashObject(Domain.LEAF, paper);
  return hexOf(d);
}

export async function hashReceipt(receipt: any): Promise<string> {
  const d = await hashObject(Domain.RECEIPT, receipt);
  return hexOf(d);
}

export async function hashResponseInitial(paperHashHex: string): Promise<string> {
  const d = await digest(Domain.RESPONSE, hexToBytes(paperHashHex));
  return hexOf(d);
}

export async function hashResponseStep(prevHashHex: string, event: any): Promise<string> {
  const d = await digest(Domain.RESPONSE, hexToBytes(prevHashHex), canonicalBytes(event));
  return hexOf(d);
}

export class ResponseChainTracker {
  public currentRHex: string;
  public events: any[];
  public paperHashHex: string;

  constructor(paperHashHex: string, initialRHex: string, events: any[] = []) {
    this.paperHashHex = paperHashHex;
    this.currentRHex = initialRHex;
    this.events = events;
  }

  static async create(paperHashHex: string): Promise<ResponseChainTracker> {
    const initial = await hashResponseInitial(paperHashHex);
    return new ResponseChainTracker(paperHashHex, initial);
  }

  async addEvent(event: any): Promise<string> {
    this.currentRHex = await hashResponseStep(this.currentRHex, event);
    this.events.push(event);
    return this.currentRHex;
  }
}
