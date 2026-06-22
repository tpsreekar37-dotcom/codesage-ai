# Future Engineering Enhancements

The platform provides a solid clean architecture layout. Here is the roadmap for extending it for enterprise usage:

## 1. OAuth2 GitHub App Integration
- **Currently**: Implements cloning of public URLs via subprocesses.
- **Future**: Authenticate users via GitHub OAuth, request repo scopes, and register a webhook to trigger automated code reviews on every git commit / Pull Request automatically.

## 2. Real-Time WebSockets
- **Currently**: The React application polls the analysis endpoint every 3 seconds to fetch status changes.
- **Future**: Connect FastAPI endpoints to a WebSocket gateway. Push review statuses, line items, and logs to the client dynamically.

## 3. Deep Codebase Context (Gemini Vector Indexing)
- **Currently**: Concatenates file files up to token constraints and feeds them to the context window.
- **Future**: Parse the files, chunk them, compute embeddings, and load them into a vector database (e.g. pgvector inside our PostgreSQL database). Use Retrieval-Augmented Generation (RAG) to query vector indexes, yielding highly precise codebase-wide security and refactoring reviews.

## 4. Multi-Tenant Sandbox Isolations
- **Currently**: Subprocesses run natively inside the FastAPI container.
- **Future**: Spin up ephemeral isolated Docker/gVisor sandboxes to execute repository clones and local code compilation checks, preventing resource leaking or code execution vulnerabilities on the host.
