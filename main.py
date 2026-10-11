import html
import re
from pathlib import Path

import yaml
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from markdown_it import MarkdownIt

app = FastAPI()
templates = Jinja2Templates(directory="templates")
md = MarkdownIt()

POSTS_DIR = Path("posts")
EXPLAINERS_DIR = Path("explainers")


def parse_post(path: Path) -> dict:
    raw = path.read_text()
    meta = {}
    content = raw
    if raw.startswith("---"):
        _, fm, body = raw.split("---", 2)
        meta = yaml.safe_load(fm) or {}
        content = body
    return {
        "slug": path.stem,
        "title": meta.get("title", path.stem.replace("-", " ").title()),
        "created": meta.get("created"),
        "updated": meta.get("updated"),
        "html": md.render(content),
    }


def list_explainers() -> list[dict]:
    """Files are named YYYY-MM-DD-<slug>.html; newest gets the bare slug on a clash."""
    result = []
    seen = set()
    for path in sorted(EXPLAINERS_DIR.glob("*.html"), reverse=True):
        date, slug = path.stem[:10], path.stem[11:]
        if slug in seen:
            slug = path.stem
        seen.add(slug)
        with path.open() as f:
            m = re.search(r"<title>(.*?)</title>", f.read(4096), re.DOTALL)
        title = html.unescape(m.group(1).strip()) if m else slug
        result.append({"slug": slug, "date": date, "title": title, "path": path})
    return result


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/posts", response_class=HTMLResponse)
async def posts(request: Request):
    post_files = sorted(POSTS_DIR.glob("*.md"), reverse=True)
    post_list = [parse_post(f) for f in post_files]
    post_list.sort(key=lambda p: p["created"] or "", reverse=True)
    return templates.TemplateResponse(request, "posts.html", {"posts": post_list})


@app.get("/posts/{slug}", response_class=HTMLResponse)
async def post(request: Request, slug: str):
    path = POSTS_DIR / f"{slug}.md"
    if not path.exists():
        return HTMLResponse("Not found", status_code=404)
    p = parse_post(path)
    return templates.TemplateResponse(request, "post.html", {"post": p})


@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse(request, "about.html")


@app.get("/explainers", response_class=HTMLResponse)
async def explainers(request: Request):
    return templates.TemplateResponse(
        request, "explainers.html", {"explainers": list_explainers()}
    )


@app.get("/explainers/{slug}")
async def explainer(slug: str):
    for e in list_explainers():
        if e["slug"] == slug:
            return FileResponse(e["path"], media_type="text/html")
    return HTMLResponse("Not found", status_code=404)
