#!/usr/bin/env python3
"""Create the small Express + React repo the routing probes run in.

    python3 prototypes/dev-kit-routing/make_fixture.py <empty-dir>

Areas: server/ (Express), client/ (React), src/config.js (shared config), docs/, resume.md
(a non-code file for the false-positive probe). Initialised as a git repo with one commit.
"""
import subprocess
import sys
from pathlib import Path

FILES = {
    "package.json": '{\n  "name": "fixture-app",\n  "private": true,\n  "scripts": {"test": "node --test"}\n}\n',
    "README.md": "# fixture-app\n\nExpress API in server/, React client in client/.\n",
    "src/config.js": (
        "const TIMEOUT = 5000;\n\n"
        "function withTimeout(promise) {\n"
        "  return Promise.race([promise, new Promise((_, r) => setTimeout(() => r(new Error('timeout')), TIMEOUT))]);\n"
        "}\n\n"
        "module.exports = { TIMEOUT, withTimeout, port: process.env.PORT || 3000 };\n"
    ),
    "server/app.js": (
        "const express = require('express');\n"
        "const login = require('./routes/login');\n\n"
        "const app = express();\napp.use(express.json());\napp.post('/login', login);\n\n"
        "module.exports = app;\n"
    ),
    "server/routes/login.js": (
        "const users = { alice: 'secret' };\n\n"
        "module.exports = function login(req, res) {\n"
        "  const { user, password } = req.body || {};\n"
        "  if (users[user] && users[user] === password) return res.json({ ok: true });\n"
        "  return res.status(401).json({ ok: false, attempts: 1 });\n"
        "};\n"
    ),
    "client/src/LoginForm.jsx": (
        "import { useState } from 'react';\n\n"
        "export default function LoginForm() {\n"
        "  const [error, setError] = useState(null);\n"
        "  async function submit(e) {\n"
        "    e.preventDefault();\n"
        "    const res = await fetch('/login', { method: 'POST', body: new FormData(e.target) });\n"
        "    const body = await res.json();\n"
        "    if (!body.ok) setError(`Login failed (attempts: ${body.attempts})`);\n"
        "  }\n"
        "  return (<form onSubmit={submit}><input name=\"user\" /><input name=\"password\" type=\"password\" />"
        "<button>Sign in</button>{error && <p>{error}</p>}</form>);\n"
        "}\n"
    ),
    "docs/api.md": "# API\n\n- `POST /login` — `{user, password}` → `{ok}` or 401 `{ok:false, attempts}`.\n",
    "resume.md": "# Jane Doe\n\n## Skills\n\n- Front-end: React, TypeScript\n- Back-end: Node.js, Express\n- Data: PostgreSQL\n",
}


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    root = Path(sys.argv[1])
    root.mkdir(parents=True, exist_ok=True)
    for rel, body in FILES.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
                    "commit", "-q", "-m", "fixture"], cwd=root, check=True)
    print(root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
