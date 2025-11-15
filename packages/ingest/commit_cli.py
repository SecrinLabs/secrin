import argparse
import sys

from packages.ingest.commit_decisions import process_repository


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Ingest commit decision docs into the graph",
    )
    parser.add_argument("repo", help="Git URL (https/ssh) or local repo path")
    parser.add_argument("-b", "--branch", help="Branch or ref to checkout", default=None)
    parser.add_argument("-m", "--max", dest="max_commits", type=int, default=None, help="Max commits to process")

    args = parser.parse_args(argv)

    summary = process_repository(args.repo, branch=args.branch, max_commits=args.max_commits)
    commit_count = summary.get('counts', {}).get('commits', 'unknown')
    author_count = summary.get('counts', {}).get('authors', 'unknown')
    print(f"Ingested {commit_count} commits ({author_count} authors) into graph.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
