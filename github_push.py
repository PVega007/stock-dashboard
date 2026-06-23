"""
github_push.py — Called by scheduled tasks after updating stock_dashboard.html
Copies the dashboard as index.html and pushes to GitHub Pages.
Uses --force and token-in-URL to handle diverged history reliably.
"""
import subprocess, shutil, datetime, os

cowork = "/Users/pvegamacbookair/Claude Cowork"

try:
    with open(f"{cowork}/github_token.txt") as f:
        token = f.read().strip()

    if not token:
        raise ValueError("github_token.txt is empty")

    # Copy dashboard as index.html (name GitHub Pages expects)
    shutil.copy(f"{cowork}/stock_dashboard.html", f"{cowork}/index.html")

    today = datetime.date.today().isoformat()
    remote = f"https://PVega007:{token}@github.com/PVega007/stock-dashboard.git"

    # Clear any stale git locks from previous crashed runs
    for lockfile in ["index.lock", "HEAD.lock"]:
        path = os.path.join(cowork, ".git", lockfile)
        if os.path.exists(path):
            os.remove(path)

    subprocess.run(["git", "-C", cowork, "add", "index.html", "stock_dashboard.html"], check=True, capture_output=True)

    # Commit — if nothing changed, git returns exit code 1; that's fine
    result = subprocess.run(
        ["git", "-C", cowork, "commit", "-m", f"Dashboard update {today}"],
        capture_output=True, text=True
    )
    if result.returncode not in (0, 1):
        raise RuntimeError(f"git commit failed: {result.stderr}")

    # Force push to handle any remote divergence
    subprocess.run(["git", "-C", cowork, "push", "--force", remote, "main"], check=True, capture_output=True)

    print("✅ GitHub Pages updated — https://pvega007.github.io/stock-dashboard is live.")

except Exception as e:
    print(f"⚠️ GitHub push failed: {e}. Dashboard saved locally — push manually if needed.")
