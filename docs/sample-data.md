# Sample Data and Seed Scripts

This directory contains sample data and seed scripts to help you test DevSecrin with realistic examples.

## Quick Start Sample Data

### 1. Sample Repository Configuration

Use the provided `.env.example` to configure a test repository:

```bash
# Copy the example configuration
cp .env.example .env

# Edit with your test repository
GITHUB_TOKEN=your_github_token
GITHUB_OWNER=microsoft
GITHUB_REPO=vscode
```

### 2. Sample Questions to Try

Once DevSecrin is running, try these example queries:

#### Code Understanding

- "What is the main architecture of this project?"
- "How does the authentication system work?"
- "What are the recent changes to the API?"

#### Development History

- "Why was feature X implemented this way?"
- "What issues are related to performance?"
- "Who are the main contributors to module Y?"

#### Documentation Discovery

- "What documentation exists for getting started?"
- "How do I contribute to this project?"
- "What are the coding standards?"

### 3. Test Repository Suggestions

For testing DevSecrin, we recommend these public repositories:

1. **Small Projects** (Quick setup):

   - `microsoft/calculator`
   - `github/docs`
   - `facebook/create-react-app`

2. **Medium Projects** (Rich context):

   - `microsoft/vscode`
   - `facebook/react`
   - `golang/go`

3. **Large Projects** (Full features):
   - `kubernetes/kubernetes`
   - `torvalds/linux`
   - `nodejs/node`

### 4. Sample Confluence/Documentation Sites

If you want to test documentation ingestion:

- **Public Wikis**: `https://en.wikipedia.org/wiki/Software_engineering`
- **Open Source Docs**: `https://docs.github.com/`
- **Technical Blogs**: Various engineering blog sites

## Seed Script Usage

### Automatic Setup

```bash
# Run the setup script (includes sample data suggestions)
python3 setup.py

# Follow the prompts to configure sample repositories
```

### Manual Setup

```bash
# 1. Configure your environment
cp .env.example .env

# 2. Edit .env with sample repository settings
# 3. Start DevSecrin
docker-compose up -d

# 4. Access the web interface
open http://localhost:3000
```

## Testing Scenarios

### Scenario 1: New Team Onboarding

1. Set up with a repository you're unfamiliar with
2. Ask questions about the codebase structure
3. Explore recent changes and their context

### Scenario 2: Code Review Context

1. Pick a recent pull request
2. Ask about the motivation behind changes
3. Explore related issues and documentation

### Scenario 3: Bug Investigation

1. Find a closed bug issue
2. Trace its resolution through commits
3. Understand the fix and related changes

## Sample Data Files

_Note: In a full implementation, this directory would contain:_

- `sample_repos.json` - List of recommended test repositories
- `sample_queries.json` - Curated list of example questions
- `seed_database.py` - Script to populate database with sample data
- `mock_integrations.py` - Mock data for testing without real APIs

## Contributing Sample Data

Help improve DevSecrin's sample data:

1. Test with interesting repositories
2. Submit effective example queries
3. Share configuration patterns that work well
4. Document interesting use cases you discover

## Troubleshooting Sample Setup

If you encounter issues with sample data:

1. **GitHub Rate Limits**: Use a personal access token
2. **Large Repositories**: Start with smaller repos for testing
3. **Documentation Sites**: Ensure the site allows scraping
4. **Local Testing**: Try the local repository analyzer first
