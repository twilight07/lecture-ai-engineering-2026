# GitHub write target policy

- Never create or submit an issue or pull request in the upstream repository `matsuolab/lecture-ai-engineering-2026`.
- The only allowed issue and pull request repository is the user's fork: `twilight07/lecture-ai-engineering-2026`.
- Before any GitHub issue or pull request write action, verify the repository owner is exactly `twilight07` and the repository is exactly `lecture-ai-engineering-2026`.
- For pull requests, set `headOwner` to `twilight07` and use the fork's `main` as the base unless the user specifies another branch within the fork.
- If the target repository, owner, or base cannot be verified as belonging to the fork, do not perform the write action. Stop and ask the user.
- Treat the `upstream` remote as read-only. Never use it as the destination for an issue or pull request.