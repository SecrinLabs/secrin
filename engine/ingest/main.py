from sqlalchemy.orm import Session
from db.index import SessionLocal
from db.models.repository import Repository
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from config import settings

async def update_vectorstore():
    session: Session = SessionLocal()
    try:
        repos = (
            session.query(Repository)
            .filter(Repository.description.isnot(None))
            .all()
        )
    except Exception as e:
        print(f"Database query failed: {e}")
        session.close()
        return None
    finally:
        session.close()

    if not repos:
        print("No repositories with descriptions found.")
        return None

    docs = []
    for repo in repos:
        raw_metadata = {
            "id": repo.id,
            "user_id": repo.user_id,
            "repo_name": repo.repo_name,
            "repo_url": repo.repo_url,
            "repo_id": repo.repo_id,
            "full_name": repo.full_name,
            "private": repo.private,
            "language": repo.language,
            "stargazers_count": repo.stargazers_count,
            "forks_count": repo.forks_count,
            "watchers_count": repo.watchers_count,
            "default_branch": repo.default_branch,
            "open_issues_count": repo.open_issues_count,
            "has_issues": repo.has_issues,
            "has_discussions": repo.has_discussions,
            "archived": repo.archived,
            "created_at": repo.created_at.isoformat() if repo.created_at else None,
            "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
            "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
            "clone_url": repo.clone_url,
            "owner_login": repo.owner_login,
            "owner_type": repo.owner_type,
        }

        # Build human-readable content with metadata included
        page_content = f"""
            Repository: {repo.repo_name}
            Full Name: {repo.full_name}
            Description: {repo.description}

            Clone URL: {repo.clone_url}
            Repo URL: {repo.repo_url}
            Owner: {repo.owner_login} ({repo.owner_type})
            Language: {repo.language}
            Private: {repo.private}

            Stars: {repo.stargazers_count}
            Forks: {repo.forks_count}
            Watchers: {repo.watchers_count}
            Open Issues: {repo.open_issues_count}
            Default Branch: {repo.default_branch}
            Archived: {repo.archived}
            Created At: {raw_metadata["created_at"]}
            Updated At: {raw_metadata["updated_at"]}
            Last Push: {raw_metadata["pushed_at"]}
            """

        try:
            doc = Document(
                page_content=page_content.strip(),
                metadata=raw_metadata,  # still keep raw metadata for filtering
            )
            docs.append(doc)

            print("DOC CREATED ----")
            print(doc.page_content[:200], "...")
            print("Metadata keys:", list(doc.metadata.keys()))

        except Exception as e:
            print(f"Skipping repo {repo.id} due to error: {e}")

    if not docs:
        print("No valid documents constructed from repositories.")
        return None

    try:
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=settings.GEMINI_API_KEY,
        )
    except Exception as e:
        print(f"Failed to initialize embeddings: {e}")
        return None

    try:
        vectorstore = Chroma.from_documents(
            documents=docs,
            embedding=embeddings,
            persist_directory="./chroma_db"
        )
        vectorstore.persist()
        print(f"Vectorstore updated with {len(docs)} documents.")
        return vectorstore
    except Exception as e:
        print(f"Vectorstore update failed: {e}")
        return None
