import requests

# ✅ GitHub GraphQL endpoint
GITHUB_API_URL = "https://api.github.com/graphql"

# ✅ GitHub token (replace securely, avoid hardcoding in production)
GITHUB_TOKEN = "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"

# ✅ GraphQL query to fetch merged PRs and their closing issues
query = """
{
  repository(owner: "calcom", name: "cal.com") {
    pullRequests(first: 10, states: MERGED, orderBy: {field: UPDATED_AT, direction: DESC}) {
      nodes {
        number
        title
        url
        mergedAt
        closingIssuesReferences(first: 5) {
          nodes {
            number
            title
            url
            closedAt
          }
        }
      }
    }
  }
}
"""

# ✅ Headers
headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}

# ✅ Make the request
response = requests.post(GITHUB_API_URL, headers=headers, json={"query": query})

# ✅ Handle response
if response.status_code == 200:
    pull_requests = response.json()["data"]["repository"]["pullRequests"]["nodes"]

    for pr in pull_requests:
        print(f"\n🟢 PR #{pr['number']}: {pr['title']}")
        print(f"🔗 {pr['url']}")
        print(f"📅 Merged At: {pr['mergedAt']}")
        
        issues = pr["closingIssuesReferences"]["nodes"]
        if issues:
            for issue in issues:
                print(f"    ↪ Closes Issue #{issue['number']}: {issue['title']}")
                print(f"      🔗 {issue['url']} (Closed at: {issue['closedAt']})")
        else:
            print("    ⚠️ No closing issues found.")
else:
    print("❌ Query failed:", response.status_code)
    print(response.text)
