/**
 * Client-side cryptographic SHA-256 verifier using Web Crypto API.
 */

export async function computeClientSha256(data: any): Promise<string> {
  const sortedJson = JSON.stringify(data, Object.keys(data).sort());
  const encoder = new TextEncoder();
  const buffer = encoder.encode(sortedJson);
  const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return '0x' + hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
}

export function formatHash(hash: string, chars = 8): string {
  if (!hash) return '';
  if (hash.length <= chars * 2 + 2) return hash;
  return `${hash.slice(0, chars + 2)}...${hash.slice(-chars)}`;
}

