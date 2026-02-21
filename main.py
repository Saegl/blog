from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from markdown_it import MarkdownIt

app = FastAPI()
templates = Jinja2Templates(directory="templates")
md = MarkdownIt()

POSTS_DIR = Path("posts")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/posts", response_class=HTMLResponse)
async def posts(request: Request):
    post_files = sorted(POSTS_DIR.glob("*.md"), reverse=True)
    post_list = [{"slug": f.stem, "title": f.stem.replace("-", " ").title()} for f in post_files]
    return templates.TemplateResponse(request, "posts.html", {"posts": post_list})


@app.get("/posts/{slug}", response_class=HTMLResponse)
async def post(request: Request, slug: str):
    path = POSTS_DIR / f"{slug}.md"
    if not path.exists():
        return HTMLResponse("Not found", status_code=404)
    content = md.render(path.read_text())
    return templates.TemplateResponse(request, "post.html", {"content": content, "title": slug.replace("-", " ").title()})


@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse(request, "about.html")
