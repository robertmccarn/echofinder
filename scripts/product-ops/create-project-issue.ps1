[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$Title,

  [Parameter(Mandatory = $true)]
  [string]$BodyFile,

  [Parameter()]
  [string]$Repo = "robertmccarn/echofinder",

  [Parameter()]
  [string]$ProjectOwner = "robertmccarn",

  [Parameter()]
  [int]$ProjectNumber = 2,

  [Parameter()]
  [string]$BoardStatus = "Backlog",

  [Parameter()]
  [string[]]$Labels = @(),

  [Parameter()]
  [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $BodyFile)) {
  throw "Body file not found: $BodyFile"
}

$gh = Get-Command gh -ErrorAction SilentlyContinue
if (-not $gh) {
  throw "GitHub CLI (gh) was not found."
}

function Invoke-GhJson {
  param([string[]]$Arguments)

  $json = & $gh.Source @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "gh command failed: gh $($Arguments -join ' ')"
  }

  return $json | ConvertFrom-Json
}

function Get-ProjectStatusMetadata {
  param(
    [int]$ProjectNumber,
    [string]$ProjectOwner,
    [string]$StatusName
  )

  $query = 'query($login:String!,$field:String!){ user(login:$login){ projectV2(number:' + $ProjectNumber + '){ id field(name:$field){ __typename ... on ProjectV2SingleSelectField{ id name options{ id name } } } } } }'
  $result = Invoke-GhJson -Arguments @("api", "graphql", "-f", "query=$query", "-f", "login=$ProjectOwner", "-f", "field=Status")
  $project = $result.data.user.projectV2
  if (-not $project) {
    throw "Project $ProjectOwner/$ProjectNumber was not found."
  }

  $statusField = $project.field
  if (-not $statusField) {
    throw "Project $ProjectOwner/$ProjectNumber does not have a Status field."
  }

  $statusOption = $statusField.options | Where-Object { $_.name -eq $StatusName } | Select-Object -First 1
  if (-not $statusOption) {
    $available = ($statusField.options | ForEach-Object { $_.name }) -join ", "
    throw "Project Status option '$StatusName' was not found. Available options: $available"
  }

  return [pscustomobject]@{
    ProjectId = $project.id
    FieldId = $statusField.id
    OptionId = $statusOption.id
  }
}

$labelArgs = @()
foreach ($label in $Labels) {
  if ($label) {
    $labelArgs += @("--label", $label)
  }
}

if ($DryRun) {
  Write-Output "Dry run: would create issue '$Title' in $Repo."
  Write-Output "Dry run: would add issue to project $ProjectOwner/$ProjectNumber with Status '$BoardStatus'."
  exit 0
}

$issueArgs = @("issue", "create", "--repo", $Repo, "--title", $Title, "--body-file", $BodyFile) + $labelArgs
$issueUrl = & $gh.Source @issueArgs
if ($LASTEXITCODE -ne 0) {
  throw "Could not create issue '$Title'."
}

$issue = Invoke-GhJson -Arguments @("issue", "view", $issueUrl, "--repo", $Repo, "--json", "number,url")

$item = Invoke-GhJson -Arguments @("project", "item-add", "$ProjectNumber", "--owner", $ProjectOwner, "--url", $issue.url, "--format", "json")
$metadata = Get-ProjectStatusMetadata -ProjectNumber $ProjectNumber -ProjectOwner $ProjectOwner -StatusName $BoardStatus

& $gh.Source project item-edit --id $item.id --project-id $metadata.ProjectId --field-id $metadata.FieldId --single-select-option-id $metadata.OptionId | Out-Null
if ($LASTEXITCODE -ne 0) {
  throw "Could not set project Status to '$BoardStatus' for issue #$($issue.number)."
}

Write-Output "Created issue #$($issue.number): $($issue.url)"
Write-Output "Added to project $ProjectOwner/$ProjectNumber with Status '$BoardStatus'."
