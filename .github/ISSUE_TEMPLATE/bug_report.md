---
name: Bug report
about: Create a report to help us improve
title: "[Bug]"
labels: bug
assignees: ''
type: Bug

---

## Bug Description
A clear and concise description of what the bug is.

## Environment & Deployment Context
Please provide details about your deployment to help us reproduce the issue.

*   **Stellar Engine Version/Commit:** (e.g., `main` branch at commit `xxxxxx`, or a specific release tag)
*   **Deployment Type:**
    *   [ ] FedRAMP High
    *   [ ] DoD IL5
    *   [ ] DoD IL4
    *   [ ] FedRAMP Moderate
    *   [ ] US Region Restricted (e.g., Access Policy constraint)
    *   [ ] Stand-alone / Custom
*   **FAST Stage (if applicable):**
    *   [ ] Stage 0 (Bootstrap)
    *   [ ] Stage 1 (Resource Management)
    *   [ ] Stage 2 (Network Creation)
    *   [ ] Stage 3 (Security & Audit)
*   **Affected Component:** (e.g., `modules/net-vpc`, `blueprints/il5/bigquery`, `fast/stage-1`)
*   **Terraform Version:** (e.g., `1.5.7`)
*   **GCP Provider Version:** (e.g., `5.10.0`)

## Steps to Reproduce
Steps to reproduce the behavior:
1. Go to '...'
2. Run command '...'
3. See error '...'

## Expected Behavior
A clear and concise description of what you expected to happen.

## Actual Behavior
A clear and concise description of what actually happened.

## Relevant Logs and Errors
Please include any relevant logs or error messages from Terraform or GCP.
```
...
```

## Additional Context
Add any other context about the problem here. E.g., does this block a specific compliance control (NIST 800-53r5)?
