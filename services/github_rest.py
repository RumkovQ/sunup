"""GitHub REST API client."""

from datetime import datetime, timezone
from typing import Optional
import aiohttp


class GitHubService:
    BASE = "https://api.github.com"

    def __init__(self, token: str, username: str = ""):
        self.token, self.username = token, username

    def _headers(self) -> dict:
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def _get(self, session: aiohttp.ClientSession, path: str, params: Optional[dict] = None):
        async with session.get(f"{self.BASE}{path}", headers=self._headers(), params=params, timeout=20) as response:
            response.raise_for_status()
            return await response.json()

    async def profile(self) -> dict:
        async with aiohttp.ClientSession() as session:
            if self.token:
                return await self._get(session, "/user")
            if not self.username:
                raise RuntimeError("Set GITHUB_USERNAME or GITHUB_TOKEN")
            return await self._get(session, f"/users/{self.username}")

    async def repositories(self) -> list[dict]:
        async with aiohttp.ClientSession() as session:
            if self.token:
                repos = await self._get(session, "/user/repos", {"affiliation": "owner,collaborator", "per_page": 100, "sort": "pushed"})
            else:
                if not self.username:
                    raise RuntimeError("Set GITHUB_USERNAME or GITHUB_TOKEN")
                repos = await self._get(session, f"/users/{self.username}/repos", {"per_page": 100, "sort": "pushed"})
        return [repo for repo in repos if not repo.get("fork")]

    async def resume(self) -> str:
        profile, repos = await self.profile(), await self.repositories()
        top = sorted(repos, key=lambda repo: repo.get("stargazers_count", 0), reverse=True)[:5]
        languages = sorted({repo["language"] for repo in repos if repo.get("language")})
        pushed = [repo.get("pushed_at") for repo in repos if repo.get("pushed_at")]
        latest = max(pushed)[:10] if pushed else "нет данных"
        lines = [f"👤 {profile.get('name') or profile.get('login')}"]
        if profile.get("bio"):
            lines.append(profile["bio"])
        lines.append("\n⭐ Топ репозиториев:")
        lines.extend(f"• {repo['name']} — {repo.get('stargazers_count', 0)} ⭐" for repo in top)
        lines.append("\n🧰 Языки: " + (", ".join(languages) or "нет данных"))
        lines.append(f"🕒 Последняя активность: {latest}")
        return "\n".join(lines)

    async def unanswered_issues(self, threshold_days: int) -> list[dict]:
        repos = await self.repositories()
        login = (self.username or (await self.profile()).get("login", "")).lower()
        candidates = []
        async with aiohttp.ClientSession() as session:
            for repo in repos:
                owner, name = repo["owner"]["login"], repo["name"]
                issues = await self._get(session, f"/repos/{owner}/{name}/issues", {"state": "open", "per_page": 100})
                for issue in issues:
                    if "pull_request" in issue:
                        continue
                    created = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
                    age = (datetime.now(timezone.utc) - created).days
                    if age < threshold_days:
                        continue
                    # GitHub's comments endpoint is needed to check whether this user participated.
                    comments = await self._get(session, f"/repos/{owner}/{name}/issues/{issue['number']}/comments", {"per_page": 100})
                    usernames = {comment.get("user", {}).get("login", "").lower() for comment in comments}
                    if not comments or login not in usernames:
                        candidates.append({"title": issue["title"], "url": issue["html_url"], "age_days": age, "repo": repo["full_name"]})
        return sorted(candidates, key=lambda issue: issue["age_days"], reverse=True)
