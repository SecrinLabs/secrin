from git import Repo
from models.gitcommit import GitCommit
from models import engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class GitScraper:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.repo = Repo(repo_path)
        self.repo_name = repo_path.strip("/").split("/")[-1]
        self.db = SessionLocal()
        GitCommit.metadata.create_all(bind=engine)

    def _get_commits(self, branch="main", max_count=100):
        return list(self.repo.iter_commits(branch, max_count=max_count))

    def _commit_exists(self, commit_hash):
        return self.db.query(GitCommit).filter_by(commit_hash=commit_hash).first() is not None

    def _extract_commit_data(self, commit):
        message = commit.message.strip()
        author = f"{commit.author.name} <{commit.author.email}>"
        date = commit.committed_datetime
        commit_hash = commit.hexsha
        files = list(commit.stats.files.keys())

        try:
            if commit.parents:
                diffs = commit.diff(commit.parents[0], create_patch=True)
            else:
                diffs = commit.diff(NULL_TREE, create_patch=True)  # handle separately or skip
        except Exception as e:
            print(f"❌ Diff error for {commit_hash}: {e}")
            diffs = []

        diff_texts = []
        for diff in diffs:
            try:
                diff_texts.append(diff.diff.decode("utf-8", errors="ignore"))
            except Exception as e:
                print(f"⚠️ Diff decode failed: {e}")

        return {
            "repo_name": self.repo_name,
            "commit_hash": commit_hash,
            "message": message,
            "author": author,
            "date": date,
            "files": files,
            "diff": "\n".join(diff_texts)
        }

    def _save_to_db(self, data):
        if self._commit_exists(data["commit_hash"]):
            print(f"♻️ Already exists: {data['commit_hash']}")
            return

        commit = GitCommit(**data)
        self.db.add(commit)
        self.db.commit()
        print(f"✅ Inserted: {data['commit_hash']}")

    def scrape(self, branch="main", max_count=100):
        commits = self._get_commits(branch, max_count)
        print(f"🔍 Found {len(commits)} commits")

        for commit in commits:
            data = self._extract_commit_data(commit)
            if not data["diff"].strip():
                print(f"⚠️ Skipped empty diff: {data['commit_hash']}")
                continue
            self._save_to_db(data)
