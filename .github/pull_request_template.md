## Description
Please include a summary of the change and which issue is fixed. Please also include relevant motivation and context.

Fixes # (GitHub issue id)

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Deployment & Compliance Impact
*   **Applicable Regimes:**
    *   [ ] US Region Restricted (e.g., Access Policy constraint)
    *   [ ] FedRAMP Moderate
    *   [ ] FedRAMP High
    *   [ ] DoD IL4
    *   [ ] DoD IL5
    *   [ ] General / All
*   **NIST 800-53r5 Controls:** (If this PR helps satisfy or modifies control implementations, list them here)

## Checklist

### Code Quality & Reusability
- [ ] My code adheres to the **Maximize Reusability** principle. I have not redefined common elements and have reused existing base configurations and modules where possible.
- [ ] I have checked that no existing module or configuration in `modules/` or `fast/` can be leveraged for this change.
- [ ] My code follows the established naming conventions outlined in `documentation/naming-convention.md`.

### Documentation
- [ ] I have updated the `README.md` of the modified module or blueprint.
- [ ] I have added/updated documentation for inputs (variables) and outputs.

### Security
- [ ] My change adheres to GCP security best practices and the principle of least privilege.
- [ ] I have ensured compliance with the targeted regime (FedRAMP High, IL5, etc.).

### Testing
- [ ] I have tested my changes locally.
- [ ] I have included details of my testing in this PR.

## Testing Performed
Please describe the tests that you ran to verify your changes.
