[CmdletBinding()]
param(
  [Parameter()]
  [string]$Repo = "robertmccarn/echofinder",

  [Parameter()]
  [ValidateSet("open", "closed", "all")]
  [string]$State = "open",

  [Parameter()]
  [int]$Limit = 50,

  [Parameter()]
  [switch]$UseGh,

  [Parameter()]
  [string]$OutputMarkdown
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Has-Gh {
  $cmd = Get-Command gh -ErrorAction SilentlyContinue
  return $null -ne $cmd
}

function Score-IssueBodyQuality {
  param([string]$Body)

  $requiredHeadings = @(
    "Problem",
    "Acceptance criteria",
    "Tasks",
    "Dependencies",
    "Validation"
  )

  $missing = @()
  foreach ($h in $requiredHeadings) {
    if ($Body -notmatch "(?im)^\s*#+\s*$([regex]::Escape($h))\s*$") {
      $missing += $h
    }
  }

  return [pscustomobject]@{
    MissingHeadings = $missing
    MissingCount = $missing.Count
  }
}

$lines = @()
$lines += "# Issue audit (read-only)"
$lines += ""
$lines += "- Repo: Repo = $Repo"
$lines += "- State: State = $State"
$lines += "- Limit: Limit = $Limit"
$lines += "- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$lines += ""

if (-not $UseGh) {
  $lines += "This script is safe by default and does not call GitHub."
  $lines += ""
  $lines += "To audit issues via GitHub CLI (read-only), re-run with:"
  $lines += ""
  $lines += "To enable GitHub CLI calls, pass -UseGh."
  $lines += (".\\scripts\\product-ops\\audit-issues.ps1 -UseGh -Repo {0} -State {1} -Limit {2}" -f $Repo, $State, $Limit)
} else {
  if (-not (Has-Gh)) {
    throw "GitHub CLI (gh) not found. Install gh or run without -UseGh."
  }

  $json = & gh issue list --repo $Repo --state $State --limit $Limit --json number,title,labels,body,url
  if ($LASTEXITCODE -ne 0) { throw "gh issue list failed. Ensure you're authenticated: gh auth status" }

  $issues = $json | ConvertFrom-Json
  $lines += "## Results"
  $lines += ""
  if (-not $issues -or $issues.Count -eq 0) {
    $lines += "_No issues returned._"
  } else {
    foreach ($i in $issues) {
      $body = if ($null -ne $i.body) { $i.body } else { "" }
      $score = Score-IssueBodyQuality -Body $body
      $labelNames = @()
      if ($null -ne $i.labels) {
        foreach ($l in $i.labels) { $labelNames += $l.name }
      }

      $status = if ($score.MissingCount -eq 0) { "OK" } else { "MISSING: " + ($score.MissingHeadings -join ", ") }
      $lines += ("- #{0} {1} ({2})" -f $i.number, $i.title, $status)
      if ($labelNames.Count -gt 0) {
        $lines += ("  - labels: {0}" -f ($labelNames -join ", "))
      }
      $lines += ("  - url: {0}" -f $i.url)
    }
  }
}

$report = ($lines -join [Environment]::NewLine)

if ($OutputMarkdown) {
  Set-Content -LiteralPath $OutputMarkdown -Value $report -Encoding UTF8
}

Write-Output $report

