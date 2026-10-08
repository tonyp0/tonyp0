"""Pull live GitHub data for the profile cards (or build a sample set for local testing)."""
import datetime as dt
import json
import os
import random
import urllib.request

API = "https://api.github.com/graphql"
MONTHS_BACK = 4


def _month_starts(today, n):
    """First day of the current month and the n-1 months before it, oldest first."""
    starts = []
    y, m = today.year, today.month
    for _ in range(n):
        starts.append(dt.date(y, m, 1))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    return list(reversed(starts))


def _next_month(d):
    return dt.date(d.year + (d.month == 12), d.month % 12 + 1, 1)


def _gql(query, variables, token):
    req = urllib.request.Request(
        API,
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json",
                 "User-Agent": "profile-cards"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        body = json.load(r)
    if body.get("errors"):
        raise RuntimeError(f"GitHub API error: {body['errors']}")
    return body["data"]


def fetch_live(login, token, today=None):
    today = today or dt.datetime.now(dt.timezone.utc).date()
    starts = _month_starts(today, MONTHS_BACK)

    month_fields = []
    for i, s in enumerate(starts):
        end = min(_next_month(s), today + dt.timedelta(days=1))
        month_fields.append(f"""
      m{i}: contributionsCollection(from: "{s}T00:00:00Z", to: "{end}T00:00:00Z") {{
        totalCommitContributions
        totalPullRequestContributions
        commitContributionsByRepository(maxRepositories: 10) {{
          repository {{ name }} contributions {{ totalCount }}
        }}
        repositoryContributions(first: 10) {{
          totalCount
          nodes {{ occurredAt repository {{ name primaryLanguage {{ name }} }} }}
        }}
      }}""")

    query = f"""
    query($login: String!) {{
      user(login: $login) {{
        login name avatarUrl
        followers {{ totalCount }}
        repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC,
                     orderBy: {{field: CREATED_AT, direction: ASC}}) {{
          nodes {{
            name description isFork diskUsage stargazerCount createdAt pushedAt url
            primaryLanguage {{ name }}
          }}
        }}
        year: contributionsCollection {{
          totalCommitContributions
          contributionCalendar {{
            totalContributions
            weeks {{ contributionDays {{ date contributionCount }} }}
          }}
        }}
        {''.join(month_fields)}
      }}
    }}"""
    u = _gql(query, {"login": login}, token)["user"]

    repos = [
        dict(name=r["name"], desc=r["description"] or "", lang=(r["primaryLanguage"] or {}).get("name"),
             size_kb=r["diskUsage"] or 0, stars=r["stargazerCount"], created=r["createdAt"][:10],
             pushed=(r["pushedAt"] or r["createdAt"])[:10], url=r["url"])
        for r in u["repositories"]["nodes"] if not r["isFork"]
    ]

    weeks = [[dict(date=d["date"], count=d["contributionCount"]) for d in w["contributionDays"]]
             for w in u["year"]["contributionCalendar"]["weeks"]]

    months = []
    for i, s in enumerate(starts):
        m = u[f"m{i}"]
        months.append(dict(
            month=s.strftime("%Y-%m"),
            commits=m["totalCommitContributions"],
            prs=m["totalPullRequestContributions"],
            commit_repos=[dict(name=c["repository"]["name"] if c["repository"] else "private repo",
                               commits=c["contributions"]["totalCount"])
                          for c in m["commitContributionsByRepository"]],
            created=[dict(name=n["repository"]["name"],
                          lang=(n["repository"]["primaryLanguage"] or {}).get("name"),
                          date=n["occurredAt"][:10])
                     for n in m["repositoryContributions"]["nodes"] if n.get("repository")],
        ))

    return dict(
        login=u["login"], name=u["name"] or u["login"], avatar_url=u["avatarUrl"],
        followers=u["followers"]["totalCount"],
        today=str(today),
        year_total=u["year"]["contributionCalendar"]["totalContributions"],
        year_commits=u["year"]["totalCommitContributions"],
        weeks=weeks, months=months, repos=repos,
    )


def fetch_sample(login, today=None):
    """Deterministic made-up data so the cards can be rendered without a token."""
    today = today or dt.date.today()
    rnd = random.Random(7)
    start = today - dt.timedelta(days=364)
    start -= dt.timedelta(days=(start.weekday() + 1) % 7)  # back up to Sunday
    weeks, week, d = [], [], start
    while d <= today:
        busy = 0.55 if d.month in (1, 2, 3, 4, 9, 10) else 0.3
        c = 0 if rnd.random() > busy else rnd.choice([1, 1, 2, 3, 4, 6, 9, 14])
        week.append(dict(date=str(d), count=c))
        if len(week) == 7:
            weeks.append(week)
            week = []
        d += dt.timedelta(days=1)
    if week:
        weeks.append(week)

    repos = [
        ("intro-to-python-labs", "Python", 410, "2025-09-02", "2025-12-05", 0, "CS1 lab work"),
        ("leetcode-journal", "Python", 260, "2026-01-11", "2026-10-06", 1, "Daily problem log"),
        ("Monetic", "Swift", 9800, "2026-04-03", "2026-10-07", 2,
         "Budgeting app that builds financial literacy for K-12 and college students"),
        ("telemetry-plotter", "Python", 1500, "2026-06-20", "2026-08-14", 0, "Plotting UAV flight logs"),
        ("ml-notebooks", "Jupyter Notebook", 22000, "2026-08-25", "2026-09-30", 0, "Course + side ML experiments"),
        ("tonyp0", "Python", 640, "2026-10-08", str(today), 0, "This profile"),
    ]
    repos = [dict(name=n, lang=l, size_kb=s, created=c, pushed=pu, stars=st, desc=de,
                  url=f"https://github.com/{login}/{n}") for n, l, s, c, pu, st, de in repos]

    months = []
    for i, s in enumerate(_month_starts(today, MONTHS_BACK)):
        commits = [18, 41, 27, 33][i]
        months.append(dict(
            month=s.strftime("%Y-%m"), commits=commits, prs=[0, 1, 0, 2][i],
            commit_repos=[[dict(name="telemetry-plotter", commits=12), dict(name="Monetic", commits=6)],
                          [dict(name="Monetic", commits=29), dict(name="ml-notebooks", commits=8),
                           dict(name="telemetry-plotter", commits=4)],
                          [dict(name="ml-notebooks", commits=15), dict(name="Monetic", commits=12)],
                          [dict(name="Monetic", commits=19), dict(name="leetcode-journal", commits=9),
                           dict(name="tonyp0", commits=5)]][i],
            created=[[], [dict(name="ml-notebooks", lang="Jupyter Notebook", date="2026-08-25")], [],
                     [dict(name="tonyp0", lang="Python", date=str(today))]][i],
        ))

    total = sum(d["count"] for w in weeks for d in w)
    return dict(login=login, name="Tony", avatar_url="", followers=12, today=str(today),
                year_total=total, year_commits=int(total * 0.9), weeks=weeks, months=months, repos=repos)


def fetch(login, sample=False):
    if sample:
        return fetch_sample(login)
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("Set GH_TOKEN (or run with --sample).")
    return fetch_live(login, token)
