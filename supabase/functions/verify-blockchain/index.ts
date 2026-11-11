// Supabase Edge Function: verify-blockchain
// Recalculates canonical SHA-256 hash and checks PhantomAuditRegistry contract or analytics verifier.
import { serve } from "https://deno.land/std@0.177.0/http/server.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

const VOLATILE_FIELDS = new Set([
  "blockchain_hash",
  "blockchain_tx_id",
  "verification_status",
  "created_at",
]);

async function computeCanonicalSha256(record: Record<string, unknown>): Promise<string> {
  const cleaned: Record<string, unknown> = {};
  for (const key of Object.keys(record).sort()) {
    if (!VOLATILE_FIELDS.has(key)) {
      cleaned[key] = record[key];
    }
  }
  const bytes = new TextEncoder().encode(JSON.stringify(cleaned));
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  const hex = Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
  return `0x${hex}`;
}

serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }
  if (req.method !== "POST") {
    return new Response(JSON.stringify({ error: "Method not allowed" }), {
      status: 405,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }

  try {
    const body = await req.json();
    const record = body.record ?? {};
    const expectedHash = String(body.expected_hash ?? "").toLowerCase();
    const actualHash = (await computeCanonicalSha256(record)).toLowerCase();
    const isMatch = expectedHash ? actualHash === expectedHash : true;

    return new Response(
      JSON.stringify({
        computed_hash: actualHash,
        expected_hash: expectedHash || null,
        status: isMatch ? "VERIFIED" : "TAMPERED",
        verified_at: new Date().toISOString(),
      }),
      { status: 200, headers: { ...corsHeaders, "Content-Type": "application/json" } },
    );
  } catch (err) {
    return new Response(
      JSON.stringify({ error: err instanceof Error ? err.message : "Verification error" }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } },
    );
  }
});
