# Scheduled report: ROSA HyperFleet CI daily health report

You are running a **cron** scheduled task that produces a daily CI health report for ROSA HyperFleet jobs. Keep the report **as concise as possible** to minimize channel noise. When everything is healthy, keep the summary concise, but still use the standard report structure. Only expand into detail when something needs attention.

## Goal

Check the pass/fail history (last 10 completed builds per job) for ROSA HyperFleet CI periodic jobs. Report overall CI health and individual job status.

- Always post the top-level status to the channel (never call `no_action_required()`)
- If all jobs are passing: post the status summary only — no threaded replies
- If any job is failing: post the status summary, then create a threaded reply per failing job with investigation

## Procedure

### 1. Load job configuration

Fetch the CI configuration from the single source of truth:
`https://raw.githubusercontent.com/openshift/release/refs/heads/main/ci-operator/config/openshift-online/rosa-hyperfleet/openshift-online-rosa-hyperfleet-main.yaml`

Use `fetch_web_content` to retrieve this YAML file. It defines all tests including periodic jobs with `cron:` schedules.

**Track these 2 periodic jobs:**

- `nightly-ephemeral` (test name `as: nightly-ephemeral`)
- `nightly-integration` (test name `as: nightly-integration`)

The full Prow job names follow the pattern:
`periodic-ci-openshift-online-rosa-hyperfleet-main-{test-name}`

If the fetch fails, fall back to these job names:

- periodic-ci-openshift-online-rosa-hyperfleet-main-nightly-ephemeral
- periodic-ci-openshift-online-rosa-hyperfleet-main-nightly-integration

### 2. Collect build history (last 10 runs)

For each job, collect the **last 10 completed job runs** for the trend table. Use Prow CI tools (`search_prow_jobs`, `query_prowjobs`, etc.) or `fetch_web_content` on the job-history page.

**Same-day reporting rule:** The "Latest Run Status" section must report **today's run** for each job. Do not fall back to a previous day's completed run for the latest status. Both jobs must be reported from the same day (today).

**Job status values:** Report the actual state of today's run:

- **passing** — today's run completed successfully
- **failing** — today's run completed with failures
- **running** — today's run is currently in progress
- **scheduled** — today's run is queued but not yet started
- **no run today** — no run was triggered today

**Retry for in-progress jobs:** If today's run for any tracked job is in a `scheduled` or `running` state:

1. Wait **10 minutes** and re-check the job status
2. Repeat up to **3 times** (30 minutes maximum wait)
3. After 30 minutes, report the current state as-is (e.g., "running" if still in progress)

**Important:** Track each of the last 10 runs with their dates:

- For each run, record: date, pass/fail status, build ID
- Format date as "MonDD" (e.g., "Jun10", "Jun11", "Jun19")
- Runs are ordered: oldest run first → newest run last (left to right)
- Count total: how many of the 10 runs passed vs failed
- Example: If 7 passed and 3 failed → "7/10 (70%)"

If Prow tools don't return historical build data directly, use `fetch_web_content` to retrieve the job-history page at `https://prow.ci.openshift.org/job-history/gs/test-platform-results/logs/%JOB_NAME%`. The HTML contains `var allBuilds = [{ID, Result, Started, Duration}];`.

### 3. Compute pass rates and health status

**Per-job pass rate**: pass/total for last 10 runs (e.g., 7/10 = 70%).

**10-run trend table**: Create a table with dates as header and jobs as rows:

- **Header row**: Dates in MonDD format (e.g., Jun10, Jun11, Jun12, ...)
- **Job rows**: Job name followed by ✅ or ❌ for each run, then pass count and percentage
- Order: oldest run first (leftmost) → newest run last (rightmost)
- Use monospace formatting for alignment

**Table format example:**

```text
              Jun10 Jun11 Jun12 Jun13 Jun14 Jun15 Jun16 Jun17 Jun18 Jun19
ephemeral:     ✅    ✅    ✅    ✅    ✅    ✅    ✅    ✅    ✅    ✅   10/10 (100%)
integration:   ✅    ✅    ❌    ✅    ✅    ✅    ✅    ✅    ❌    ❌    7/10 (70%)
```

**Overall CI health** (based on today's run status for each job):

- :large_green_circle: Both jobs passing (2/2) - both today's runs completed successfully
- :large_yellow_circle: Mixed status (1/2) - one passing, one failing/running/scheduled
- :red_circle: Both jobs failing (0/2) - both today's runs failed
- :hourglass_flowing_sand: Pending — one or both jobs still running/scheduled (after retries exhausted)
- :white_circle: No runs today — no runs were triggered today for either job

**Individual job health** (based on today's run):

- :large_green_circle: Today's run passed
- :red_circle: Today's run failed
- :hourglass_flowing_sand: Today's run is still running or scheduled (after retries exhausted)
- :white_circle: No run triggered today

### 4. Channel response (top-level summary)

Post a concise summary as your channel response. Use concise job names: "ephemeral" and "integration".

**Emoji key:** :large_green_circle: passing, :red_circle: failing, :large_yellow_circle: mixed, :hourglass_flowing_sand: running/scheduled, :white_circle: no run today.

```text
%OVERALL_EMOJI% *CI Daily — %DATE%*
%JOB_EMOJI% ephemeral: %STATUS% (<%URL%|run>)  |  %JOB_EMOJI% integration: %STATUS% (<%URL%|run>)

              Jun10 Jun11 Jun12 Jun13 Jun14 Jun15 Jun16 Jun17 Jun18 Jun19
ephemeral:     ✅    ✅    ✅    ✅    ✅    ✅    ✅    ✅    ✅    ✅   10/10 (100%)
integration:   ✅    ✅    ❌    ✅    ✅    ✅    ✅    ✅    ❌    ❌    7/10 (70%)
```

Use monospace/code block formatting for the trend table. Align columns for readability.

### 5. Failure analysis (threaded replies — only when jobs are failing)

**Skip this step entirely if both jobs are passing.** Only create threaded replies when a job has failed.

After your top-level summary (Step 4), emit `---THREAD_DETAILS---` on its own line. Everything after that delimiter becomes threaded replies (not part of the channel summary). Separate each threaded reply with `---THREAD_BREAK---` on its own line.

For each job whose **latest run failed**, produce a **separate threaded reply** with investigation. Follow the investigation procedure in `.claude/agents/ci-troubleshooter.md` to diagnose the failure. The source is `main` — read files directly with the Read tool.

Format each threaded reply like:

```text
%EMOJI% *%JOB_NAME% -- %PASS%/10 (%RATE%%)*

%SHORT_SUMMARY%
%ROOT_CAUSE_ANALYSIS%

Most recent failure: <%JOB_RUN_URL%|Build #%NUMBER%> (%DATE%)
```

Use concise job names: "ephemeral" or "integration".

**Example output with threads:**

```text
:large_yellow_circle: *CI Daily — Jun 30*
:large_green_circle: ephemeral: passing (<url|run>)  |  :red_circle: integration: failing (<url|run>)

              Jun21 Jun22 Jun23 Jun24 Jun25 Jun26 Jun27 Jun28 Jun29 Jun30
ephemeral:     ✅    ✅    ✅    ✅    ✅    ✅    ✅    ✅    ✅    ✅   10/10 (100%)
integration:   ✅    ✅    ❌    ✅    ✅    ✅    ✅    ✅    ❌    ❌    7/10 (70%)

---THREAD_DETAILS---

:red_circle: *integration -- 7/10 (70%)*

E2E test `TestClusterCreation` timed out waiting for hosted cluster to become ready.
Root cause: MC maestro-agent pod in CrashLoopBackOff due to MQTT connection failure.

Most recent failure: <url|Build #1234> (Jun 30)
```

## Constraints

- Keep the top-level summary under 2000 characters. All detailed analysis goes in threaded replies.
- If more than half the jobs return no data, warn about possible Prow/GCS issues at the top.
