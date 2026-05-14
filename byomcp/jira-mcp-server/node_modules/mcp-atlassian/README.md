# MCP Atlassian Server

A Model Context Protocol (MCP) server for integrating with Atlassian products (Confluence and Jira). This server provides tools for AI assistants to interact with Atlassian Cloud APIs, enabling document management, search, and export capabilities.

## Features

### Confluence Integration
- **Read & Search**: Access pages, spaces, and content
- **Content Management**: Create, update pages and comments
- **Page Hierarchy**: Navigate parent/child page relationships
- **Export**: Export pages as HTML or Markdown with embedded images
- **Attachments**: List, download, and upload attachments
- **Labels**: Manage page labels
- **Users**: Find and query users, track personal activity
- **Personal Dashboard**: View recent pages and mentions

### Jira Integration  
- **Issues**: Read and search issues, get personal tasks
- **Projects**: List and explore projects
- **Boards & Sprints**: List boards, view sprints, track active work
- **Comments**: Add comments to issues
- **Issue Creation**: Create new issues with custom fields
- **User Management**: Get current user details
- **Personal Dashboard**: View your open issues and sprint tasks

## Installation

### Option 1: Clone and Build (Recommended)

```bash
# Clone the repository
git clone https://github.com/Vijay-Duke/mcp-atlassian.git
cd mcp-atlassian

# Install dependencies
npm install

# Build TypeScript
npm run build
```

### Option 2: Install from GitHub

```bash
# Install directly from GitHub
npm install -g github:Vijay-Duke/mcp-atlassian

# Or install in your project
npm install github:Vijay-Duke/mcp-atlassian
```

### Option 3: NPM Registry

```bash
# Install globally
npm install -g mcp-atlassian

# Or install locally
npm install mcp-atlassian
```

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
ATLASSIAN_BASE_URL=https://yourdomain.atlassian.net
ATLASSIAN_EMAIL=your-email@example.com
ATLASSIAN_API_TOKEN=your-api-token
```

### Getting API Token

1. Log in to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Give it a label and copy the token
4. Use this token in your `.env` file

### MCP Settings Configuration

Add to your Claude Desktop config file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

#### Option 1: After npm install -g

```json
{
  "mcpServers": {
    "mcp-atlassian": {
      "command": "npx",
      "args": ["mcp-atlassian"],
      "env": {
        "ATLASSIAN_BASE_URL": "https://yourdomain.atlassian.net",
        "ATLASSIAN_EMAIL": "your-email@example.com",
        "ATLASSIAN_API_TOKEN": "YOUR_API_TOKEN"
      }
    }
  }
}
```

#### Option 2: From Local Clone

```json
{
  "mcpServers": {
    "mcp-atlassian": {
      "command": "node",
      "args": ["/path/to/your/mcp-atlassian/dist/index.js"],
      "env": {
        "ATLASSIAN_BASE_URL": "https://yourdomain.atlassian.net",
        "ATLASSIAN_EMAIL": "your-email@example.com",
        "ATLASSIAN_API_TOKEN": "YOUR_API_TOKEN"
      }
    }
  }
}
```

**Example with typical paths:**
```json
{
  "mcpServers": {
    "mcp-atlassian": {
      "command": "node",
      "args": ["~/projects/mcp-atlassian/dist/index.js"],
      "env": {
        "ATLASSIAN_BASE_URL": "https://yourdomain.atlassian.net",
        "ATLASSIAN_EMAIL": "your.email@company.com",
        "ATLASSIAN_API_TOKEN": "YOUR_API_TOKEN"
      }
    }
  }
}
```

#### Option 3: Direct from GitHub using uvx (Coming Soon)

You can run the server directly from GitHub without cloning:

```json
{
  "mcpServers": {
    "mcp-atlassian": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/Vijay-Duke/mcp-atlassian.git", "mcp-atlassian"],
      "env": {
        "ATLASSIAN_BASE_URL": "https://yourdomain.atlassian.net",
        "ATLASSIAN_EMAIL": "your-email@example.com",
        "ATLASSIAN_API_TOKEN": "YOUR_API_TOKEN"
      }
    }
  }
}
```

**Note:** The uvx method requires the package to be properly configured for Python packaging. This is planned for a future release.

## Available Tools

### Confluence Tools

| Tool | Description |
|------|-------------|
| `get_confluence_current_user` | Get details of the authenticated user |
| `get_confluence_user` | Get details for a specific user |
| `search_confluence_pages_by_user` | Search pages by user activity |
| `list_user_confluence_pages` | List pages authored by a user |
| `list_user_confluence_attachments` | List attachments uploaded by a user |
| `read_confluence_page` | Read a Confluence page by ID or title |
| `search_confluence_pages` | Search pages using CQL (Confluence Query Language) |
| `list_confluence_spaces` | List all accessible spaces |
| `get_confluence_space` | Get details of a specific space |
| `create_confluence_page` | Create a new page |
| `update_confluence_page` | Update existing page content |
| `list_confluence_page_children` | List child pages of a page |
| `list_confluence_page_ancestors` | Get parent hierarchy of a page |
| `export_confluence_page` | Export page as HTML or Markdown with embedded images |
| `list_confluence_attachments` | List page attachments |
| `download_confluence_attachment` | Download specific attachment |
| `upload_confluence_attachment` | Upload file to a page |
| `download_confluence_page_complete` | Download page with all content |
| `add_confluence_comment` | Add comment to a page |
| `list_confluence_page_labels` | Get page labels |
| `add_confluence_page_label` | Add labels to a page |
| `find_confluence_users` | Search for users |
| `get_my_recent_confluence_pages` | List your recent pages |
| `get_confluence_pages_mentioning_me` | Find pages that mention you |

### Jira Tools

| Tool | Description |
|------|-------------|
| `get_jira_current_user` | Get details of the authenticated user |
| `get_jira_user` | Get details for a specific user |
| `search_jira_issues_by_user` | Search issues by user involvement |
| `list_user_jira_issues` | List issues by user role with date filtering |
| `get_user_jira_activity` | Track user activity including comments and transitions |
| `get_user_jira_worklog` | Get time tracking entries with formatted totals |
| `read_jira_issue` | Read issue details by key |
| `search_jira_issues` | Search issues using JQL |
| `list_jira_projects` | List all accessible projects |
| `create_jira_issue` | Create new issue |
| `add_jira_comment` | Add comment to issue |
| `list_jira_boards` | List accessible Scrum/Kanban boards |
| `list_jira_sprints` | List sprints for a board |
| `get_jira_sprint` | Get detailed sprint information |
| `get_my_tasks_in_current_sprint` | Get your tasks in active sprints |
| `get_my_open_issues` | Get all your open issues |

## Usage Examples

### Export Confluence Page

```javascript
// Export as HTML (raw content with embedded images)
{
  "tool": "export_confluence_page",
  "arguments": {
    "pageId": "123456789",
    "format": "html"
  }
}

// Export as Markdown with metadata
{
  "tool": "export_confluence_page",
  "arguments": {
    "pageId": "123456789",
    "format": "markdown"
  }
}
```

### Search Confluence

```javascript
{
  "tool": "search_confluence_pages",
  "arguments": {
    "cql": "space=DEV AND text~'architecture'",
    "limit": 10
  }
}
```

### Create Jira Issue

```javascript
{
  "tool": "create_jira_issue",
  "arguments": {
    "projectKey": "PROJ",
    "issueType": "Task",
    "summary": "Implement new feature",
    "description": "Detailed description here",
    "priority": "Medium"
  }
}
```

### Get Your Sprint Tasks

```javascript
// Get your tasks in the current sprint
{
  "tool": "get_my_tasks_in_current_sprint",
  "arguments": {
    "projectKey": "PROJ"
  }
}

// Get all your open issues
{
  "tool": "get_my_open_issues",
  "arguments": {
    "projectKeys": ["PROJ1", "PROJ2"],
    "maxResults": 50
  }
}
```

### Work with Boards and Sprints

```javascript
// List boards for a project
{
  "tool": "list_jira_boards",
  "arguments": {
    "projectKeyOrId": "PROJ",
    "type": "scrum"
  }
}

// Get active sprints for a board
{
  "tool": "list_jira_sprints",
  "arguments": {
    "boardId": 123,
    "state": "active"
  }
}
```

### User-Specific Jira Operations

```javascript
// Get user details
{
  "tool": "get_jira_user",
  "arguments": {
    "username": "john.doe"
  }
}

// Search issues by user involvement
{
  "tool": "search_jira_issues_by_user",
  "arguments": {
    "username": "john.doe",
    "searchType": "assignee",
    "status": "In Progress",
    "maxResults": 20
  }
}

// Get user's work logs
{
  "tool": "get_user_jira_worklog",
  "arguments": {
    "username": "john.doe",
    "startDate": "2024-01-01",
    "endDate": "2024-01-31",
    "projectKeys": ["PROJ1", "PROJ2"]
  }
}

// Track user activity
{
  "tool": "get_user_jira_activity",
  "arguments": {
    "username": "john.doe",
    "activityType": "all",
    "days": 7
  }
}
```

## Content Format Support

### Markdown ↔ Confluence Storage Format

The server automatically converts between Markdown and Confluence's storage format:
- Write content in Markdown when creating/updating pages
- Read pages in either storage format or converted to Markdown
- Preserves formatting, links, and structure

### Export Formats

- **HTML**: Raw Confluence HTML with all images embedded as base64 data URIs
- **Markdown**: Clean Markdown with YAML frontmatter, includes metadata and embedded images

## Development

```bash
# Run TypeScript compiler in watch mode
npm run dev

# Build for production
npm run build

# Run tests (if available)
npm test
```

## Project Structure

```
mcp-atlassian/
├── src/
│   ├── index.ts                 # Main server entry point
│   ├── types/                   # TypeScript type definitions
│   ├── confluence/
│   │   ├── handlers.ts          # Confluence API handlers
│   │   └── tools.ts             # Tool definitions
│   ├── jira/
│   │   ├── handlers.ts          # Jira API handlers
│   │   └── tools.ts             # Tool definitions
│   └── utils/
│       ├── http-client.ts       # Axios HTTP client setup
│       ├── content-converter.ts # Markdown ↔ Storage conversion
│       └── export-converter.ts  # HTML/Markdown export utilities
├── dist/                        # Compiled JavaScript
├── .env                         # Environment variables (not in git)
├── package.json
└── tsconfig.json
```

## Security Notes

- API tokens are stored in environment variables, never in code
- Uses Basic Authentication with API tokens (not passwords)
- All requests are made over HTTPS
- Supports Atlassian Cloud only (not Server/Data Center)

## Limitations

- No delete operations implemented (by design for safety)
- Export to PDF requires browser conversion (HTML → Print → PDF)
- Some Confluence macros may not convert perfectly to Markdown
- Rate limits apply based on Atlassian Cloud API limits

## CI/CD Pipeline

This project uses GitHub Actions for continuous integration and deployment.

### Workflows

#### 🔄 Continuous Integration (`ci.yml`)
- **Triggers**: Push to main/develop, Pull requests
- **Jobs**:
  - **Test**: Runs tests on Node.js 18.x, 20.x, and 22.x
  - **Build**: Compiles TypeScript and validates the build
  - **Lint**: Type checking and security audit
  - **Validate Package**: Ensures package size and structure

#### 📦 Publish to npm (`publish.yml`)
- **Triggers**: GitHub releases, Manual dispatch
- **Features**:
  - Automatic version bumping
  - npm publishing with provenance
  - GitHub release creation
  - Changelog updates

#### 🔒 Security Scanning (`security.yml`)
- **Triggers**: Push to main, PRs, Weekly schedule
- **Scans**:
  - npm audit for vulnerabilities
  - CodeQL analysis
  - OWASP dependency check
  - Snyk security scanning (optional)

#### 🏷️ Release Management (`release.yml`)
- **Triggers**: Version tags, Manual dispatch
- **Features**:
  - Automatic changelog generation
  - GitHub release creation
  - Build artifacts attachment
  - Release notes formatting

#### ✅ PR Validation (`pr-validation.yml`)
- **Triggers**: Pull request events
- **Checks**:
  - Semantic PR title validation
  - PR size labeling
  - Auto-labeling based on files changed

### 🤖 Automated Dependency Updates

Dependabot is configured to:
- Check for npm dependency updates weekly
- Check for GitHub Actions updates weekly
- Group non-major updates together
- Create PRs with proper labels

### Setting Up CI/CD

#### Required GitHub Secrets

1. **NPM_TOKEN**: npm authentication token for publishing
   - Generate at: https://www.npmjs.com/settings/YOUR_USERNAME/tokens
   - Required scopes: `publish`

2. **SNYK_TOKEN** (Optional): For Snyk security scanning
   - Get from: https://app.snyk.io/account

#### Branch Protection

Recommended branch protection rules for `main`:
- Require PR reviews before merging
- Require status checks to pass (CI tests)
- Require branches to be up to date
- Include administrators in restrictions

### Local Development

Before pushing changes:

```bash
# Run tests locally
npm test

# Build the project
npm run build

# Check for security vulnerabilities
npm audit

# Type check
npx tsc --noEmit
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Create an issue in the GitHub repository
- Check Atlassian API documentation for API-specific questions
- Review MCP documentation for protocol-related topics

## Acknowledgments

Built with:
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io)
- [Atlassian REST APIs](https://developer.atlassian.com/cloud/)
- TypeScript, Node.js, Axios