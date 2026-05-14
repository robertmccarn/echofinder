[CmdletBinding()]
param(
  [Parameter()]
  [string]$Root = (Get-Location).Path,

  [Parameter()]
  [string[]]$Paths = @("README.md", "docs"),

  [Parameter()]
  [switch]$Quiet,

  [Parameter()]
  [string]$OutputMarkdown
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-MarkdownFiles {
  param([string]$RootDir, [string[]]$InputPaths)

  foreach ($p in $InputPaths) {
    $full = Join-Path $RootDir $p
    if (Test-Path -LiteralPath $full -PathType Leaf) {
      if ($full.ToLowerInvariant().EndsWith(".md")) { Get-Item -LiteralPath $full }
      continue
    }
    if (Test-Path -LiteralPath $full -PathType Container) {
      Get-ChildItem -LiteralPath $full -Recurse -File -Filter *.md -ErrorAction SilentlyContinue
      continue
    }
  }
}

function Extract-RelativeLinks {
  param([string]$Text)

  $links = @()
  $inlineMatches = [regex]::Matches($Text, "\[[^\]]*\]\(([^)]+)\)")
  foreach ($m in $inlineMatches) {
    $links += $m.Groups[1].Value
  }
  return $links
}

function Is-CheckableLink {
  param([string]$Href)

  if ([string]::IsNullOrWhiteSpace($Href)) { return $false }

  $trim = $Href.Trim()
  if ($trim.StartsWith("http://") -or $trim.StartsWith("https://")) { return $false }
  if ($trim.StartsWith("mailto:")) { return $false }
  if ($trim.StartsWith("#")) { return $false }
  if ($trim.StartsWith("file:")) { return $false }

  return $true
}

function Strip-Anchor {
  param([string]$Href)

  $idx = $Href.IndexOf("#")
  if ($idx -lt 0) { return $Href }
  return $Href.Substring(0, $idx)
}

$mdFiles = @(Get-MarkdownFiles -RootDir $Root -InputPaths $Paths | Sort-Object FullName -Unique)
if ($mdFiles.Count -eq 0) {
  throw "No Markdown files found under: $($Paths -join ', ')"
}

$missing = New-Object System.Collections.Generic.List[object]

foreach ($file in $mdFiles) {
  $content = Get-Content -LiteralPath $file.FullName -Raw
  $dir = Split-Path -Parent $file.FullName

  foreach ($href in (Extract-RelativeLinks -Text $content)) {
    if (-not (Is-CheckableLink -Href $href)) { continue }

    $noAnchor = Strip-Anchor -Href $href
    if ([string]::IsNullOrWhiteSpace($noAnchor)) { continue }

    $candidate = Join-Path $dir $noAnchor
    $resolved = Resolve-Path -LiteralPath $candidate -ErrorAction SilentlyContinue
    if (-not $resolved) {
      $missing.Add([pscustomobject]@{
        File = $file.FullName
        Link = $href
      }) | Out-Null
    }
  }
}

$lines = @()
$lines += "# Doc link check"
$lines += ""
$lines += "- Root: Root = $Root"
$lines += "- Paths: $($Paths -join ', ')"
$lines += "- Markdown files scanned: $($mdFiles.Count)"
$lines += ""

if ($missing.Count -eq 0) {
  $lines += "OK: No missing relative link targets found."
} else {
  $lines += "MISSING: Missing relative link targets:"
  $lines += ""
  foreach ($m in $missing) {
    $lines += "- File: $($m.File) -> Link: $($m.Link)"
  }
}

$report = ($lines -join [Environment]::NewLine)

if ($OutputMarkdown) {
  Set-Content -LiteralPath $OutputMarkdown -Value $report -Encoding UTF8
}

if (-not $Quiet) {
  Write-Output $report
}

if ($missing.Count -gt 0) {
  exit 2
}
