[CmdletBinding()]
param(
  [Parameter()]
  [string]$BaseRef,

  [Parameter()]
  [string]$HeadRef = "HEAD",

  [Parameter()]
  [string]$RepoRoot = (Get-Location).Path,

  [Parameter()]
  [string]$OutputMarkdown
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Push-Location $RepoRoot
try {
  if (-not $BaseRef) {
    $hasOriginTestMain = (& git rev-parse --verify --quiet origin/test-main) -ne $null
    if ($hasOriginTestMain) {
      $BaseRef = "origin/test-main"
    } else {
      $BaseRef = "test-main"
    }
  }

  $range = "$BaseRef..$HeadRef"

  $commits = & git log $range --no-merges --pretty=format:"%h|%s"
  if ($LASTEXITCODE -ne 0) { throw "git log failed for range: $range" }

  $commitLines = @()
  foreach ($line in $commits) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    $parts = $line.Split("|", 2)
    $sha = $parts[0]
    $subj = $parts[1]
    $commitLines += "- `$sha` $subj"
  }

  $lines = @()
  $lines += "# Sprint summary"
  $lines += ""
  $lines += "- Range: `$range`"
  $lines += "- Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")"
  $lines += ""
  if ($commitLines.Count -eq 0) {
    $lines += "_No commits found in range._"
  } else {
    $lines += "## Commits"
    $lines += ""
    $lines += $commitLines
  }

  $report = ($lines -join "`n")

  if ($OutputMarkdown) {
    Set-Content -LiteralPath $OutputMarkdown -Value $report -Encoding UTF8
  }

  Write-Output $report
} finally {
  Pop-Location
}

