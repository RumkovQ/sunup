"""GitHub contribution streak calculation using GraphQL calendar data."""

import aiohttp
from datetime import date, timedelta


class GitHubGraphQL:
    URL = "https://api.github.com/graphql"

    def __init__(self, token: str, username: str):
        self.token, self.username = token, username

    async def current_streak(self) -> tuple[int, bool]:
        if not self.token or not self.username:
            raise RuntimeError("GITHUB_TOKEN and GITHUB_USERNAME are required for the contribution streak")
        query = """query($login:String!, $from:DateTime!, $to:DateTime!) {
          user(login:$login) { contributionsCollection(from:$from,to:$to) {
            contributionCalendar { weeks { contributionDays { date contributionCount } } }
          } }
        }"""
        today = date.today()
        headers = {"Authorization": f"Bearer {self.token}"}

        async def load_window(session, start: date, end: date) -> dict[date, int]:
            variables = {
                "login": self.username,
                "from": f"{start.isoformat()}T00:00:00Z",
                "to": f"{end.isoformat()}T23:59:59Z",
            }
            async with session.post(
                self.URL,
                json={"query": query, "variables": variables},
                headers=headers,
                timeout=20,
            ) as response:
                response.raise_for_status()
                payload = await response.json()
            if payload.get("errors"):
                raise RuntimeError(payload["errors"][0].get("message", "GitHub GraphQL error"))
            days = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
            return {
                date.fromisoformat(day["date"]): day["contributionCount"]
                for week in days
                for day in week["contributionDays"]
                if start <= date.fromisoformat(day["date"]) <= end
            }

        has_today = False
        current = today
        streak = 0
        window_end = today
        async with aiohttp.ClientSession() as session:
            while True:
                # GitHub rejects contribution ranges longer than one year. A 364-day
                # difference safely includes 365 calendar dates, including leap years.
                window_start = window_end - timedelta(days=364)
                counts = await load_window(session, window_start, window_end)
                if window_end == today:
                    has_today = counts.get(today, 0) > 0
                    current = today if has_today else today - timedelta(days=1)

                while current >= window_start:
                    if counts.get(current, 0) <= 0:
                        return streak, has_today
                    streak += 1
                    current -= timedelta(days=1)

                # The entire window was active; fetch the previous one to avoid
                # under-reporting streaks longer than a year.
                window_end = window_start - timedelta(days=1)
        return streak, has_today
