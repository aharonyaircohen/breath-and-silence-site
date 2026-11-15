# Public website instructions

Read README.md before edits. This repository is PUBLIC and serves a static site from docs/. The private course repository is canonical; content/ is a reviewed publication snapshot, not a parallel course authority.

- Preserve Yair's approved model terms and distinguish findings, interpretation and hypotheses.
- Research item IDs must remain stable. All counts are derived from content/research.json; bibliographic items are not all supportive experiments.
- Public data uses an explicit allowlist. Never copy private research/library.json, provenance, source archives, long quotations, local paths, participant data, credentials or chats into this repository.
- Generate docs/ with scripts/build.py. Do not hand-edit generated HTML as a separate source.
- Test before commit: python3 -m unittest discover -s tests -v. Verify source links, route base, search, RTL, mobile and browser console. Read back exact remote content and live site after publication.
- Keep original content at stable paths and use Git history. No extra numbered review copies or public build logs containing system data.
- Changes to public claims require explicit review; no medical assurances, recovered-memory claims or enforced emotional discharge.
