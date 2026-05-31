# Rollback Instructions

If a deployment fails or you need to revert to the previous release, follow these steps.

Frontend (Vercel)
1. In Vercel dashboard, open your project → Deployments.
2. Find the previous successful deployment (the Vercel action logs a deployment URL and a Git commit). Click **Promote** or **Restore** to roll back to that deployment.
3. Optionally, redeploy by selecting the desired commit and clicking **Redeploy**.

Backend (Railway)
1. In Railway dashboard, open the project and service.
2. Select the previous successful deployment from the deployments list.
3. Click **Rollback** (or redeploy the earlier commit) to restore the previous release.

Automated rollback (GitHub Actions)
- You can implement an automated rollback step in `deployment.yml` that triggers when post-deploy health checks fail. A simple approach is:
  - Keep the previous image tag (e.g., `rag-backend:<sha>` of last success) recorded in a persistent store (artifact or tag).
  - If health checks fail, re-deploy the previous image via Railway CLI: `railway up --project <id> --service <id> --image ghcr.io/<owner>/rag-backend:<previous-sha>`

Notes
- Always ensure your environment variables and secrets are consistent between releases.
- Test rollback steps in a staging environment before relying on them in production.
