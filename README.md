#  VitePress Generator Service API

This service clones a repository, reads its README, scaffolds a VitePress project, and starts the VitePress development server.

### Start the Server
```bash
uvicorn app:app --reload --port 8001
```
*(Note: Use a different port if running alongside `app.py`, e.g., 8001)*

### Usage

**Generate and Serve Documentation:**
Send a POST request to `/generate-vitepress`.

```bash
curl -X POST http://localhost:8000/generate-vitepress \
     -H "Content-Type: application/json" \
     -d '{"repo_url": "https://github.com/username/repo"}'
```

**What happens:**
1.  The repo is cloned to a temporary directory.
2.  The `README.md` is extracted.
3.  A VitePress project is created in `vitepress_documentation`.
4.  Dependencies are installed (`npm install`).
5.  The docs are served (`npm run docs:dev`).

### Directory Structure

*   `app.py`: Logic for VitePress scaffolding and serving.
*   `vitepress_documentation/`: Output directory for the generated docs site.