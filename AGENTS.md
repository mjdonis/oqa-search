# Agent Guide for oqa-search

## Project Scope

CLI tool to automate searching openQA test results and build checks for SUSE updates. Generates copy-paste formatted output for QA update logs.

**What it does:**
- Searches openQA for test jobs related to an update ID
- Fetches build check results for packages in the update
- Formats results for easy inclusion in update reports

**What it doesn't do:**
- Does not trigger tests or builds
- Does not modify anything in openQA or QAM
- Read-only tool, purely for information gathering

## Domain Context

**Update ID formats:** 
- `SUSE:Maintenance:XXXXX:XXXXXX` or `S:M:XXXXX:XXXXXX`
- `SUSE:SLFO:XX:YY`

**Job Groups:**
- Single Incidents: Individual update testing
- Aggregated Updates: Multiple updates tested together

## Design

- Uses regex patterns for build checks (supports multiple test frameworks)
- Defaults to 5 days for aggregated search (balance between finding results and performance)
- URL encoding properly handles special chars in package names
- Condensed output when five or more build check results to avoid long output
