# PHANTOM — System Architecture

See [docs/architecture.md](docs/architecture.md) for the full architecture specification, dual-mode design (`local` vs `cloud`), and subsystem contracts.

```
Vercel / Browser (React 18 + Cytoscape.js)
   ├── Supabase Cloud (PostgreSQL 15+ 18 Tables, 8 PL/pgSQL Functions, RLS, Edge Functions)
   ├── Python FastAPI Microservice (NetworkX + Pandas + 8-Factor Explainable Risk Engine)
   ├── Neo4j Aura (Property Graph, NetworkX fallback in local mode)
   └── EVM Blockchain (PhantomAuditRegistry.sol, Hardhat in local mode / Sepolia in cloud mode)
```
