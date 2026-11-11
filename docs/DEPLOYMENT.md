# PHANTOM — Cloud Deployment Guide

This guide covers deploying PHANTOM across managed cloud services (**zero Docker, zero Kubernetes**).

---

## 1. Supabase (PostgreSQL, Auth, RLS, Storage, Edge Functions)

1. Create a new project at [supabase.com](https://supabase.com).
2. In the **SQL Editor**, execute migrations in order:
   - `supabase/migrations/20261006000001_initial_schema.sql`
   - `supabase/migrations/20261006000002_advanced_analytics.sql`
   - `supabase/migrations/20261006000003_rls_policies.sql`
   - `supabase/seed.sql`
3. Under **Storage**, create private buckets: `transaction-imports`, `investigation-reports`, `evidence`.
4. Under **Authentication > URL Configuration**, add your Vercel deployment URL.
5. Deploy Edge Functions (`supabase functions deploy calculate-risk verify-blockchain health ingest-transactions generate-report`).
6. Set Edge Function secrets: `ANALYTICS_API_URL`, `ANALYTICS_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`.

**Environment variables**:
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `DATABASE_URL`

---

## 2. Neo4j Aura (Property Graph)

1. Create a free Neo4j AuraDB instance at [neo4j.com/cloud/aura](https://neo4j.com/cloud/aura/).
2. Copy the `neo4j+s://` URI, username (`neo4j`), and generated password.
3. Run idempotent graph projection:
   ```bash
   PHANTOM_MODE=cloud python scripts/sync_neo4j.py
   ```

**Environment variables**:
- `NEO4J_URI`
- `NEO4J_USER`
- `NEO4J_PASSWORD`

---

## 3. Python Analytics Microservice (Railway / Render)

1. Connect the repository and set root directory to `analytics`.
2. **Build Command**: `pip install -r requirements.txt`
3. **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**Environment variables**:
- `PHANTOM_MODE=cloud`
- `DATABASE_URL`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
- `ANALYTICS_API_KEY`
- `CORS_ORIGINS=https://your-vercel-app.vercel.app`

---

## 4. EVM Smart Contract (Ethereum Sepolia)

```bash
cd blockchain
npm install
npx hardhat run scripts/deploy.ts --network sepolia
```

**Environment variables**:
- `SEPOLIA_RPC_URL`
- `DEPLOYER_PRIVATE_KEY`
- `PHANTOM_CONTRACT_ADDRESS` (output from deploy script)

---

## 5. Frontend SPA (Vercel)

1. Import repository in Vercel with **Framework Preset**: `Vite`, **Root Directory**: `frontend`.
2. **Build Command**: `npm run build` | **Output Directory**: `dist`.
3. Configure environment variables:
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_PUBLISHABLE_KEY`
   - `VITE_ANALYTICS_API_URL`
   - `VITE_ENABLE_DEMO_MODE=false` (or `true` for public demo)

