# Security

Do not post captured sessions, secrets or exploit payloads in public issues. Report vulnerabilities privately through [GitHub private vulnerability reporting](https://github.com/alexdevmotion/grudges/security/advisories/new).

Treat captures, Git objects, build workspaces and replay outputs as private. Deleting a working file does not delete its snapshot. Review task code and Dockerfiles before execution. Use provider API keys with appropriate limits; do not copy consumer login files into containers. Shareable task authoring and report rendering still require human review before publication.

Local subscription runners are for trusted tasks. The agent runs on the host; a fresh workspace does not isolate it from other host files, global instructions or configuration. Claude uses restricted file tools; Codex uses its native workspace sandbox. Offline Docker verification happens afterward. Keep native login files in their normal location; Grudges does not copy them into containers.

This alpha has no security support SLA. Only the latest alpha is intended for fixes.
