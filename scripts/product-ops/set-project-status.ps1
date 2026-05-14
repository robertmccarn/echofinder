[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [int]$IssueNumber,

  [Parameter(Mandatory = $true)]
  [ValidateSet("Backlog", "Ready", "In Progress", "Review", "Pending Release", "Blocked", "Done")]
  [string]$BoardStatus,

  [Parameter()]
  [string]$Repo = "robertmccarn/echofinder",

  [Parameter()]
  [string]$ProjectOwner = "robertmccarn",

  [Parameter()]
  [int]$ProjectNumber = 2,

  [Parameter()]
  [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

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

function Get-ProjectItemForIssue {
  param(
    [int]$ProjectNumber,
    [string]$ProjectOwner,
    [int]$IssueNumber
  )

  $query = 'query($login:String!){ user(login:$login){ projectV2(number:' + $ProjectNumber + '){ items(first:100){ nodes{ id content{ __typename ... on Issue{ number url } } } } } } }'
  $result = Invoke-GhJson -Arguments @("api", "graphql", "-f", "query=$query", "-f", "login=$ProjectOwner")
  $items = $result.data.user.projectV2.items.nodes
  return $items | Where-Object { $_.content.__typename -eq "Issue" -and $_.content.number -eq $IssueNumber } | Select-Object -First 1
}

$issue = Invoke-GhJson -Arguments @("issue", "view", "$IssueNumber", "--repo", $Repo, "--json", "number,title,url")
$metadata = Get-ProjectStatusMetadata -ProjectNumber $ProjectNumber -ProjectOwner $ProjectOwner -StatusName $BoardStatus
$item = Get-ProjectItemForIssue -ProjectNumber $ProjectNumber -ProjectOwner $ProjectOwner -IssueNumber $IssueNumber

if (-not $item) {
  if ($DryRun) {
    Write-Output "Dry run: would add issue #$IssueNumber to project $ProjectOwner/$ProjectNumber."
  } else {
    $item = Invoke-GhJson -Arguments @("project", "item-add", "$ProjectNumber", "--owner", $ProjectOwner, "--url", $issue.url, "--format", "json")
  }
}

if ($DryRun) {
  Write-Output "Dry run: would set issue #$IssueNumber Status to '$BoardStatus'."
  exit 0
}

& $gh.Source project item-edit --id $item.id --project-id $metadata.ProjectId --field-id $metadata.FieldId --single-select-option-id $metadata.OptionId | Out-Null
if ($LASTEXITCODE -ne 0) {
  throw "Could not set project Status to '$BoardStatus' for issue #$IssueNumber."
}

Write-Output "Set issue #$IssueNumber ($($issue.title)) to '$BoardStatus' on project $ProjectOwner/$ProjectNumber."
