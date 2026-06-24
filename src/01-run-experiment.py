#!/usr/bin/env python3
"""
Lab 05 - GraphQL vs REST: Experiment Runner

This script performs a controlled experiment comparing GitHub's REST API vs GraphQL API.
For each repository, it queries the same data using both APIs and measures:
  - Response time (milliseconds)
  - Response size (bytes)

Usage:
    python src/01-run-experiment.py [--repos N] [--trials T] [--output PATH]
"""

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple
import urllib.error
import urllib.request

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Constants ────────────────────────────────────────────────────────
GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
GITHUB_REST_URL = "https://api.github.com"
DEFAULT_REPOS = 50
DEFAULT_TRIALS = 10
DEFAULT_OUTPUT = "data/results_experiment.csv"
HTTP_TIMEOUT = 60
HTTP_MAX_RETRIES = 3
WARM_UP_REQUESTS = 2


# ── Queries ──────────────────────────────────────────────────────────

# Query 1: Repository basic info (simple query)
GRAPHQL_REPO_INFO = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    nameWithOwner
    description
    url
    stargazerCount
    forkCount
    createdAt
    updatedAt
    primaryLanguage {
      name
    }
    issues(states: [OPEN, CLOSED]) {
      totalCount
    }
    pullRequests {
      totalCount
    }
    watchers {
      totalCount
    }
    releases {
      totalCount
    }
  }
}
"""

# Query 2: Repository with issues list (medium query)
GRAPHQL_REPO_ISSUES = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    nameWithOwner
    stargazerCount
    issues(first: 20, orderBy: {field: CREATED_AT, direction: DESC}) {
      totalCount
      nodes {
        title
        state
        createdAt
        closedAt
        author {
          login
        }
        labels(first: 5) {
          nodes {
            name
          }
        }
        comments {
          totalCount
        }
      }
    }
  }
}
"""

# Query 3: Repository with PRs and reviews (complex query)
GRAPHQL_REPO_PRS = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    nameWithOwner
    stargazerCount
    pullRequests(first: 10, orderBy: {field: CREATED_AT, direction: DESC}, states: [MERGED, CLOSED]) {
      totalCount
      nodes {
        title
        state
        createdAt
        mergedAt
        closedAt
        additions
        deletions
        changedFiles
        author {
          login
        }
        reviews(first: 5) {
          totalCount
          nodes {
            state
            author {
              login
            }
          }
        }
        comments(first: 5) {
          totalCount
          nodes {
            body
            author {
              login
            }
          }
        }
      }
    }
  }
}
"""

QUERY_TYPES = {
    "simple": {
        "graphql": GRAPHQL_REPO_INFO,
        "description": "Repository basic info",
    },
    "medium": {
        "graphql": GRAPHQL_REPO_ISSUES,
        "description": "Repository with issues list",
    },
    "complex": {
        "graphql": GRAPHQL_REPO_PRS,
        "description": "Repository with PRs and reviews",
    },
}


# ── Helper functions ─────────────────────────────────────────────────

def _get_github_token() -> str:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError(
            "GITHUB_TOKEN não encontrado. "
            "Configure a variável de ambiente ou use um arquivo .env"
        )
    return token


def _http_request(url: str, token: str, method: str = "GET",
                  data: bytes | None = None) -> Tuple[bytes, float]:
    """Make an HTTP request and return (response_body, elapsed_ms)."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)

    for attempt in range(1, HTTP_MAX_RETRIES + 1):
        try:
            start = time.perf_counter()
            with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
                body = response.read()
            elapsed_ms = (time.perf_counter() - start) * 1000
            return body, elapsed_ms
        except urllib.error.HTTPError as exc:
            if exc.code in {403, 429} and attempt < HTTP_MAX_RETRIES:
                wait = min(2 ** attempt, 64)
                print(f"  Rate limited ({exc.code}), waiting {wait}s...", file=sys.stderr)
                time.sleep(wait)
                continue
            if exc.code >= 500 and attempt < HTTP_MAX_RETRIES:
                wait = min(2 ** attempt, 32)
                print(f"  Server error ({exc.code}), retrying in {wait}s...", file=sys.stderr)
                time.sleep(wait)
                continue
            raise
        except urllib.error.URLError as exc:
            if attempt < HTTP_MAX_RETRIES:
                wait = min(2 ** attempt, 32)
                print(f"  Network error, retrying in {wait}s...", file=sys.stderr)
                time.sleep(wait)
                continue
            raise

    raise RuntimeError("Max retries exceeded")


def fetch_top_repos(token: str, count: int) -> List[Dict[str, str]]:
    """Fetch top repositories by stars using the REST API search endpoint."""
    repos: List[Dict[str, str]] = []
    page = 1
    per_page = min(count, 100)

    print(f"Fetching top {count} repositories by stars...", file=sys.stderr)

    while len(repos) < count:
        url = (
            f"{GITHUB_REST_URL}/search/repositories"
            f"?q=stars:>10000&sort=stars&order=desc"
            f"&per_page={per_page}&page={page}"
        )
        body, _ = _http_request(url, token)
        data = json.loads(body)
        items = data.get("items", [])
        if not items:
            break

        for item in items:
            full_name = item["full_name"]
            owner, name = full_name.split("/", 1)
            repos.append({"owner": owner, "name": name, "full_name": full_name})
            if len(repos) >= count:
                break

        print(f"  Page {page}: collected {len(repos)}/{count} repos", file=sys.stderr)
        page += 1
        time.sleep(0.5)

    return repos[:count]


def measure_graphql(
    token: str, owner: str, name: str, query: str
) -> Tuple[float, int]:
    """Execute a GraphQL query and return (elapsed_ms, response_size_bytes)."""
    payload = json.dumps({
        "query": query,
        "variables": {"owner": owner, "name": name},
    }).encode("utf-8")

    body, elapsed_ms = _http_request(
        GITHUB_GRAPHQL_URL, token, method="POST", data=payload
    )
    return elapsed_ms, len(body)


def measure_rest_simple(
    token: str, owner: str, name: str
) -> Tuple[float, int]:
    """REST equivalent of the 'simple' GraphQL query: get repo info."""
    url = f"{GITHUB_REST_URL}/repos/{owner}/{name}"
    body, elapsed_ms = _http_request(url, token)
    return elapsed_ms, len(body)


def measure_rest_medium(
    token: str, owner: str, name: str
) -> Tuple[float, int]:
    """REST equivalent of 'medium' GraphQL: repo info + issues list.
    Requires 2 REST calls (repo + issues)."""
    total_ms = 0.0
    total_size = 0

    # Call 1: Get repo info
    url1 = f"{GITHUB_REST_URL}/repos/{owner}/{name}"
    body1, ms1 = _http_request(url1, token)
    total_ms += ms1
    total_size += len(body1)

    # Call 2: Get issues
    url2 = f"{GITHUB_REST_URL}/repos/{owner}/{name}/issues?state=all&per_page=20&sort=created&direction=desc"
    body2, ms2 = _http_request(url2, token)
    total_ms += ms2
    total_size += len(body2)

    return total_ms, total_size


def measure_rest_complex(
    token: str, owner: str, name: str
) -> Tuple[float, int]:
    """REST equivalent of 'complex' GraphQL: repo + PRs + reviews.
    Requires multiple REST calls."""
    total_ms = 0.0
    total_size = 0

    # Call 1: Get repo info
    url1 = f"{GITHUB_REST_URL}/repos/{owner}/{name}"
    body1, ms1 = _http_request(url1, token)
    total_ms += ms1
    total_size += len(body1)

    # Call 2: Get pull requests
    url2 = f"{GITHUB_REST_URL}/repos/{owner}/{name}/pulls?state=closed&per_page=10&sort=created&direction=desc"
    body2, ms2 = _http_request(url2, token)
    total_ms += ms2
    total_size += len(body2)

    # Calls 3..N: Get reviews for each PR
    prs = json.loads(body2)
    for pr in prs[:10]:
        pr_number = pr.get("number")
        if pr_number:
            url_reviews = f"{GITHUB_REST_URL}/repos/{owner}/{name}/pulls/{pr_number}/reviews?per_page=5"
            body_r, ms_r = _http_request(url_reviews, token)
            total_ms += ms_r
            total_size += len(body_r)

            url_comments = f"{GITHUB_REST_URL}/repos/{owner}/{name}/pulls/{pr_number}/comments?per_page=5"
            body_c, ms_c = _http_request(url_comments, token)
            total_ms += ms_c
            total_size += len(body_c)

    return total_ms, total_size


REST_MEASURES = {
    "simple": measure_rest_simple,
    "medium": measure_rest_medium,
    "complex": measure_rest_complex,
}


def run_warm_up(token: str, owner: str, name: str) -> None:
    """Perform warm-up requests to stabilize network conditions."""
    for _ in range(WARM_UP_REQUESTS):
        try:
            url = f"{GITHUB_REST_URL}/repos/{owner}/{name}"
            _http_request(url, token)
        except Exception:
            pass
        time.sleep(0.2)


def run_experiment(
    repos: List[Dict[str, str]],
    token: str,
    trials: int,
    output_path: Path,
) -> None:
    """Run the full experiment and write results to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "repo",
        "query_type",
        "api_type",
        "trial",
        "response_time_ms",
        "response_size_bytes",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        total = len(repos) * len(QUERY_TYPES) * 2 * trials
        completed = 0

        for repo_idx, repo in enumerate(repos, 1):
            owner, name = repo["owner"], repo["name"]
            full_name = repo["full_name"]
            print(
                f"\n[{repo_idx}/{len(repos)}] {full_name}",
                file=sys.stderr,
            )

            # Warm up
            run_warm_up(token, owner, name)

            for query_type, query_info in QUERY_TYPES.items():
                graphql_query = query_info["graphql"]
                rest_fn = REST_MEASURES[query_type]

                for trial in range(1, trials + 1):
                    # ── GraphQL measurement ──
                    try:
                        gql_time, gql_size = measure_graphql(
                            token, owner, name, graphql_query
                        )
                        writer.writerow({
                            "repo": full_name,
                            "query_type": query_type,
                            "api_type": "graphql",
                            "trial": trial,
                            "response_time_ms": round(gql_time, 3),
                            "response_size_bytes": gql_size,
                        })
                        completed += 1
                    except Exception as exc:
                        print(
                            f"  ERROR GraphQL {query_type} trial {trial}: {exc}",
                            file=sys.stderr,
                        )

                    # Small delay between GraphQL and REST
                    time.sleep(0.3)

                    # ── REST measurement ──
                    try:
                        rest_time, rest_size = rest_fn(token, owner, name)
                        writer.writerow({
                            "repo": full_name,
                            "query_type": query_type,
                            "api_type": "rest",
                            "trial": trial,
                            "response_time_ms": round(rest_time, 3),
                            "response_size_bytes": rest_size,
                        })
                        completed += 1
                    except Exception as exc:
                        print(
                            f"  ERROR REST {query_type} trial {trial}: {exc}",
                            file=sys.stderr,
                        )

                    # Delay between trials
                    time.sleep(0.5)

                    # Progress
                    pct = (completed / total) * 100
                    print(
                        f"  {query_type} trial {trial}/{trials} done "
                        f"({pct:.1f}% overall)",
                        file=sys.stderr,
                    )

        csvfile.flush()

    print(f"\nExperiment complete. {completed} measurements saved to {output_path}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Lab 05 — GraphQL vs REST experiment runner"
    )
    parser.add_argument(
        "--repos", type=int, default=DEFAULT_REPOS,
        help=f"Number of repositories to test (default: {DEFAULT_REPOS})",
    )
    parser.add_argument(
        "--trials", type=int, default=DEFAULT_TRIALS,
        help=f"Number of trials per query per repo (default: {DEFAULT_TRIALS})",
    )
    parser.add_argument(
        "--output", type=str, default=DEFAULT_OUTPUT,
        help=f"Output CSV path (default: {DEFAULT_OUTPUT})",
    )

    args = parser.parse_args()
    project_root = Path(__file__).resolve().parent.parent
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = project_root / output_path

    token = _get_github_token()
    repos = fetch_top_repos(token, args.repos)

    if not repos:
        print("ERROR: No repositories found.", file=sys.stderr)
        sys.exit(1)

    print(f"\nStarting experiment with {len(repos)} repos, {args.trials} trials each...", file=sys.stderr)
    print(f"Query types: {', '.join(QUERY_TYPES.keys())}", file=sys.stderr)
    print(f"Output: {output_path}", file=sys.stderr)

    run_experiment(repos, token, args.trials, output_path)


if __name__ == "__main__":
    main()
