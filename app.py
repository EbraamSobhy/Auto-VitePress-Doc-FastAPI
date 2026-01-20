from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import shutil
import git
import json
import subprocess

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # your frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RepoRequest(BaseModel):
    repo_url: str

OUTPUT_DIR = "vitepress_documentation"
ZIP_NAME = "vitepress_docs"

def setup_vitepress(repo_name: str, readme_content: str, output_path: str):
    """
    Node-24-compatible VitePress scaffolding
    """
    docs_dir = os.path.join(output_path, "docs")
    vitepress_config_dir = os.path.join(docs_dir, ".vitepress")
    
    os.makedirs(vitepress_config_dir, exist_ok=True)
    
    # package.json
    package_json = {
        "name": f"{repo_name}-docs",
        "version": "1.0.0",
        "private": True,
        "engines": {
            "node": ">=18 <=24"
        },
        "scripts": {
            "docs:dev": "vitepress dev docs",
            "docs:build": "vitepress build docs",
            "docs:preview": "vitepress preview docs"
        },
        "devDependencies": {
            "vitepress": "^1.5.0"
        }
    }
    
    with open(os.path.join(output_path, "package.json"), "w") as f:
        json.dump(package_json, f, indent=2)
    
    # index.md
    frontmatter = "---\nlayout: doc\n---\n\n"
    with open(os.path.join(docs_dir, "index.md"), "w", encoding="utf-8") as f:
        f.write(frontmatter + readme_content)
    
    # vitepress config
    config_content = f"""import {{ defineConfig }} from 'vitepress'

export default defineConfig({{
  title: "{repo_name}",
  description: "Documentation for {repo_name}",
  themeConfig: {{
    nav: [{{ text: 'Home', link: '/' }}],
    sidebar: [{{ text: 'Guide', items: [{{ text: 'Introduction', link: '/' }}] }}],
    socialLinks: []
  }}
}})
"""
    with open(os.path.join(vitepress_config_dir, "config.mts"), "w") as f:
        f.write(config_content)


@app.post("/generate-vitepress")
def generate_vitepress(data: RepoRequest):
    temp_repo = "repo-vitepress"
    
    # Cleanup previous
    if os.path.exists(temp_repo):
        shutil.rmtree(temp_repo)
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    if os.path.exists(f"{ZIP_NAME}.zip"):
        os.remove(f"{ZIP_NAME}.zip")
    
    try:
        # Clone repo
        print(f"Cloning {data.repo_url}...")
        git.Repo.clone_from(data.repo_url, temp_repo)
        
        readme_content = "# No README found"
        repo_name = data.repo_url.split("/")[-1].replace(".git", "")
        
        # Find README
        for file in os.listdir(temp_repo):
            if file.lower().startswith("readme"):
                with open(os.path.join(temp_repo, file), "r", encoding="utf-8") as f:
                    readme_content = f.read()
                break
        
        # Create VitePress
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        setup_vitepress(repo_name, readme_content, OUTPUT_DIR)

        # Copy LICENSE / CONTRIBUTING if present
        for file in os.listdir(temp_repo):
            if file.lower() in ["license", "license.md", "license.txt",
                                "contributing", "contributing.md"]:
                shutil.copy(
                    os.path.join(temp_repo, file),
                    os.path.join(OUTPUT_DIR, "docs", file)
                )

        # Node-24-compatible: npm install, then dev
        subprocess.run(
            "npm install",
            cwd=OUTPUT_DIR,
            shell=True,
            check=True
        )

        # Zip output
        shutil.make_archive(ZIP_NAME, "zip", OUTPUT_DIR)

        return {
            "status": "success",
            "message": "VitePress documentation generated successfully.",
            "output_directory": os.path.abspath(OUTPUT_DIR),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_repo):
            shutil.rmtree(temp_repo)


@app.get("/download-vitepress")
def download_vitepress():
    file_path = f"{ZIP_NAME}.zip"
    if os.path.exists(file_path):
        return FileResponse(path=file_path, filename=f"{ZIP_NAME}.zip", media_type="application/zip")
    raise HTTPException(status_code=404, detail="Zip file not found")
