---
title: Hello World | Building My Blog with NixOS + FastAPI
created: 2026-02-21
updated: 2026-02-21
---

# Hello World | Building My Blog with NixOS + FastAPI

There were many attempts to start my blog, I honestly lost count.  
Hopefully this one lasts longer.  

This time I wanted something simple, reproducible, fast and fun to maintain.  
Here is how I set it up.

## Stack

- Domain: Namecheap
- VPS: Linode Nanode
- OS: NixOS
- Web: Nginx + Let's Encrypt
- Backend: FastAPI + markdown-it-py

## Domain

I bought domain [saegl.me](https://saegl.me) at [namecheap.com](https://namecheap.com). It costs $10 and needs yearly renewal  
I chose namecheap because it is quite popular and has cheap in its name  
All I need to configure in namecheap is `Advanced DNS` to point to my VPS

```
A Record * 172.236.220.83 Automatic
A Record @ 172.236.220.83 Automatic
```

This points all requests to domain `saegl.me` and all subdomain requests like `dev.saegl.me` to my VPS IP `172.236.220.83` that I rent with linode.
Now that DNS points to the VPS, here's how the server is set up.

## VPS + OS

I use NixOS so my entire server is defined declaratively.
I rent VPS at [linode.com](https://linode.com). This one is `Nanode 1 GB` at
$5/month. One nice thing about them, they have [NixOS guide](https://www.linode.com/docs/guides/install-nixos-on-linode/) that I prefer to use as my OS.
After that guide you will have ssh root access to your vps

Initial configuration took some time, about an hour. But after that I have just one file `configuration.nix` that defines my whole OS,
here are snippets from it:

```nix
{
  networking.hostName = "malganis";
  networking.usePredictableInterfaceNames = false;
  networking.useDHCP = false;
  networking.interfaces.eth0.useDHCP = true;
  networking.firewall.allowedTCPPorts = [22 80 443];
  environment.systemPackages = with pkgs; [
    neovim
    wget
    htop
    git
    inetutils
    uv
  ];

  services.openssh = {
    enable = true;
    settings.PermitRootLogin = "prohibit-password";
    settings.PasswordAuthentication = false;
    settings.KbdInteractiveAuthentication = false;
  };
  users.users.root.openssh.authorizedKeys.keys = [
    "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAID3mq6jo73DWU/soz5MM4hSh0q61HiDxBk2apfMDNsWV saegl@protonmail.com"
  ];
}
```

Entire configuration could be found at [malganis](https://github.com/Saegl/malganis)

As you see from the snippet, I can configure my hostname, open firewall ports and install programs in single place. 
Unlike traditional Linux setups, where configuration is often scattered across the filesystem.

So when I need to update my VPS, I do this on my laptop
```bash
cd projects/nix/malganis
nvim configuration.nix  # to change config
just deploy
```

`just` is task runner, but actually just alias for
```just
deploy:
    nixos-rebuild switch --target-host root@saegl.me --flake .#malganis
```

That will build VPS OS image locally and update remote machine. I don't need manual ssh, git pull, apt install or whatever to update my remote system


## Web services

Another interesting thing you can find in the configuration is this

```nix
{
  security.acme.acceptTerms = true;
  security.acme.defaults.email = "saegl@protonmail.com";
  services.nginx = {
    enable = true;
    virtualHosts."saegl.me" = {
      default = true;
      enableACME = true;
      forceSSL = true;
      locations."/".proxyPass = "http://127.0.0.1:8000";
    };
    virtualHosts."dev.saegl.me" = {
      enableACME = true;
      forceSSL = true;
      locations."/".return = ''200 "dev.saegl.me is alive\n"'';
      extraConfig = ''default_type text/plain;'';
    };
  }
}
```

Nginx configuration is also inside `configuration.nix`, it is reverse proxy that can point outside request to domains that we configured earlier to local services.
It also gives me https encryption with Let's Encrypt

One of the services is this blog
```nix
{
  systemd.services.blog = {
    description = "Blog FastAPI app";
    after = ["network.target"];
    wantedBy = ["multi-user.target"];
    serviceConfig = {
      WorkingDirectory = "/root/blog";
      ExecStart = "${pkgs.uv}/bin/uv run fastapi run --port 8000";
      Restart = "always";
      RestartSec = 5;
    };
  };
}
```
As you see it starts it when machine restarts or service dies. That acts as a system supervisor for my app/service.
And to easily update service source, I inject this script to my VPS

```nix
{
  environment.systemPackages = with pkgs; [
    (writeShellScriptBin "deploy-blog" ''
      set -e
      cd /root/blog
      ${git}/bin/git pull
      systemctl restart blog
      echo "Blog deployed successfully"
    '')
  ];
}
```

And so my `just` runner can update service with `just deploy`

```just
deploy:
    ssh root@saegl.me deploy-blog
```

You can imagine how it is just pulls source code on VPS and restarts systemd unit almost immediately

## Blog software
I decided to build my own blog backend and frontend. There are many good complete options like `jekyll`, `hugo` and others if you want to deploy from markdown
files on your own VPS. But I decided that I want more fun maintaining with FastAPI app, and so here it is:

[blog app](https://github.com/saegl/blog)

FastAPI builds posts from markdown and puts them in Jinja templates, here is another snippet now from python backend source

```python
@app.get("/posts/{slug}", response_class=HTMLResponse)
async def post(request: Request, slug: str):
    path = POSTS_DIR / f"{slug}.md"
    if not path.exists():
        return HTMLResponse("Not found", status_code=404)
    p = parse_post(path)
    return templates.TemplateResponse(request, "post.html", {"post": p})
```

The FastAPI code reads blogs posts like this one from posts dir

```markdown
---
title: Hello World
created: 2026-02-21
updated: 2026-02-21
---

# Hello World | Building My Blog with NixOS + FastAPI

There were many attempts to start my blog ...

...
```

And then renders it with `markdown-it-py` and `jinja` to this templates:

Base template
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}blog{% endblock %}</title>
    <style>
        body { font-family: monospace; max-width: 700px; margin: 0 auto; padding: 1rem; }
        nav { margin-bottom: 2rem; }
        nav a { margin-right: 1rem; }
        a { color: #333; }
    </style>
</head>
<body>
    <nav>
        <a href="/">root</a>
        <a href="/posts">posts</a>
        <a href="/about">about</a>
    </nav>
    {% block content %}{% endblock %}
</body>
</html>
```

Post template
```html
{% extends "base.html" %}
{% block title %}{{ post.title }}{% endblock %}
{% block content %}
<p>
    {% if post.created %}created: {{ post.created }}{% endif %}
    {% if post.updated %} | updated: {{ post.updated }}{% endif %}
</p>
{{ post.html | safe }}
{% endblock %}
```

## Conclusions

It is pretty easy to have my blog online.  
Change few files in VPS config and then do 
```bash
just deploy
```  
Or change few files in blog repo and then do
```bash
just deploy
```
It costs me 2 free github repos, 1 domain for $10/year, 1 VPS for $5/month and infinite NixOS/python tinkering

