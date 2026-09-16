# Martin Raeburn — LinkedIn Automation

Direct LinkedIn personal-profile publishing automation for Martin Raeburn using LinkedIn's official API.

## Principles

- LinkedIn-native content, not Bluesky cross-posts.
- Complex thinking, simple language.
- British English; commercially and technically literate.
- No invented experience, clients, facts, statistics or sources.
- No generic engagement bait or corporate filler.
- Political content remains neutral and factual.
- Silence is preferable to weak content.

## Planned architecture

- `voice.py` — canonical Martin Raeburn voice.
- `linkedin.py` — LinkedIn API client and member identity.
- `post.py` — original LinkedIn post generation and publishing.
- `intelligence.py` — duplicate, reputation and content-quality gates.
- `memory.py` — durable content/performance memory.
- `oauth.py` — OAuth helper; credentials are never committed.
- `.github/workflows/linkedin.yml` — scheduled/manual GitHub Actions.

## Required GitHub secrets

Do not commit credentials. The automation will use repository secrets for LinkedIn and OpenAI credentials.

The LinkedIn developer application must have `w_member_social`; OpenID Connect (`openid`, `profile`, `email`) is used for member identity.

Publishing remains disabled until OAuth credentials/tokens are configured and a controlled test succeeds.
