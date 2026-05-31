# Deployment Workflow Report

Created: `.github/workflows/deployment.yml`

Purpose
- Automatically deploy frontend to Vercel and backend to Railway after a successful CI run.

Summary of workflow steps
1. Trigger: `workflow_run` events for `Backend CI` and `Frontend CI` when they complete.
2. Verify both workflows' latest runs on `main` succeeded (via GitHub API).
3. Deploy frontend using `amondnet/vercel-action` with `VERCEL_TOKEN`, `VERCEL_ORG_ID`, and `VERCEL_PROJECT_ID`.
4. Deploy backend using Railway CLI and `RAILWAY_API_KEY`, `RAILWAY_PROJECT_ID`, `RAILWAY_SERVICE_ID`.
5. Verify `FRONTEND_URL` and `BACKEND_URL/health` are reachable.

Required GitHub secrets for deployment (summary)
- VERCEL_TOKEN
- VERCEL_ORG_ID
- VERCEL_PROJECT_ID
- RAILWAY_API_KEY
- RAILWAY_PROJECT_ID
- RAILWAY_SERVICE_ID
- FRONTEND_URL
- BACKEND_URL

How to validate the run
- In Actions UI, inspect the `Continuous Deployment` workflow run.
- Confirm the `Ensure both CI workflows succeeded` step passed.
- Confirm `Deploy frontend to Vercel` completed and returned a deployment URL (Vercel action prints the deployment URL in logs).
- Confirm `Deploy backend to Railway` step completed without errors.
- Confirm `Verify deployments` step printed `Frontend ok` and `Backend health ok`.

If any step fails
- The workflow is configured with `concurrency` to avoid overlapping deployments.
- If a deployment fails, review logs, fix the issue, and re-run the workflow manually from the Actions UI.
