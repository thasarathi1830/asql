// Supabase Edge Function: health
// Cross-service health check for Supabase Edge runtime + Python Analytics Engine.
import { serve } from "https://deno.land/std@0.177.0/http/server.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  const analyticsUrl = Deno.env.get("ANALYTICS_API_URL") ?? "";
  let analyticsStatus = "unconfigured";

  if (analyticsUrl) {
    try {
      const resp = await fetch(`${analyticsUrl}/api/health`);
      analyticsStatus = resp.ok ? "healthy" : `degraded (${resp.status})`;
    } catch {
      analyticsStatus = "unreachable";
    }
  }

  return new Response(
    JSON.stringify({
      status: "ok",
      service: "phantom-edge-health",
      analytics: analyticsStatus,
      timestamp: new Date().toISOString(),
    }),
    { status: 200, headers: { ...corsHeaders, "Content-Type": "application/json" } },
  );
});
