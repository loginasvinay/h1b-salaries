# H1B Salary Database — website

Static site: H-1B and PERM salary data from U.S. DOL OFLC public disclosure files
(FY2023–FY2026). Live at https://h1bsalary.clearinfohub.com

- 1,920,736 certified H-1B filings · 121,549 employers
- 464,379 PERM decisions · 77,632 employers
- 2,000 employer pages each side, role/state/city pages, compare tool,
  "Check my offer" tool, PERM trends + denials dashboards

## How it updates

The generator pipeline lives separately (DOL xlsx → SQLite → static HTML).
When DOL publishes a new quarterly file, the site is regenerated and pushed
here; the host redeploys automatically on every push. No server, no database.

## Data note

Wages shown are employer-attested offered wages from public records, not
verified salaries. General information only — not legal, financial, or
career advice. See /disclaimer.html and /privacy.html on the site.
