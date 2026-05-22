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
  $fallbackGhPaths = @(
    "C:\Tools\gh\gh.exe",
    "C:\Program Files\GitHub CLI\gh.exe"
  )
  foreach ($path in $fallbackGhPaths) {
    if (Test-Path -LiteralPath $path) {
      $gh = Get-Command $path -ErrorAction SilentlyContinue
      break
    }
  }
}
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

function Get-ProjectSingleSelectMetadata {
  param(
    [int]$ProjectNumber,
    [string]$ProjectOwner,
    [string]$FieldName,
    [string]$OptionName
  )

  $query = 'query($login:String!,$field:String!){ user(login:$login){ projectV2(number:' + $ProjectNumber + '){ id field(name:$field){ __typename ... on ProjectV2SingleSelectField{ id name options{ id name } } } } } }'
  $result = Invoke-GhJson -Arguments @("api", "graphql", "-f", "query=$query", "-f", "login=$ProjectOwner", "-f", "field=$FieldName")
  $project = $result.data.user.projectV2
  if (-not $project) {
    throw "Project $ProjectOwner/$ProjectNumber was not found."
  }

  $field = $project.field
  if (-not $field) {
    throw "Project $ProjectOwner/$ProjectNumber does not have a $FieldName field."
  }

  $option = $field.options | Where-Object { $_.name -eq $OptionName } | Select-Object -First 1
  if (-not $option) {
    $available = ($field.options | ForEach-Object { $_.name }) -join ", "
    throw "Project $FieldName option '$OptionName' was not found. Available options: $available"
  }

  return [pscustomobject]@{
    ProjectId = $project.id
    FieldId = $field.id
    OptionId = $option.id
  }
}

function Get-IssueLabels {
  param(
    [int]$IssueNumber,
    [string]$Repo
  )

  $issue = Invoke-GhJson -Arguments @("issue", "view", "$IssueNumber", "--repo", $Repo, "--json", "labels")
  return @($issue.labels | ForEach-Object { [string]$_.name })
}

function Get-ExpectedPriorityOptionName {
  param([string[]]$Labels)
  $labelsLower = @($Labels | ForEach-Object { $_.ToLowerInvariant() })

  if ($labelsLower -contains "prio:p0" -or $labelsLower -contains "priority/p0" -or $labelsLower -contains "priority-critical") { return "P0 - Critical" }
  if ($labelsLower -contains "prio:p1" -or $labelsLower -contains "priority/p1" -or $labelsLower -contains "priority-high") { return "P1 - High" }
  if ($labelsLower -contains "prio:p2" -or $labelsLower -contains "priority/p2" -or $labelsLower -contains "priority-medium") { return "P2 - Medium" }
  if ($labelsLower -contains "prio:stretch" -or $labelsLower -contains "priority/p3" -or $labelsLower -contains "priority-low") { return "P3 - Low" }

  return $null
}

function Get-ExpectedWorkstreamOptionName {
  param([string[]]$Labels)
  $labelsLower = @($Labels | ForEach-Object { $_.ToLowerInvariant() })

  if ($labelsLower -contains "ws:backend" -or $labelsLower -contains "workstream/backend" -or $labelsLower -contains "backend/api-access") { return "api-access" }
  if ($labelsLower -contains "ws:scoring" -or $labelsLower -contains "ws:data" -or $labelsLower -contains "ws:recommendations" -or $labelsLower -contains "workstream/engine" -or $labelsLower -contains "core-data") { return "core-data" }
  if ($labelsLower -contains "ws:docs" -or $labelsLower -contains "workstream/docs" -or $labelsLower -contains "docs/documentation") { return "documentation" }
  if ($labelsLower -contains "ws:frontend" -or $labelsLower -contains "workstream/frontend" -or $labelsLower -contains "frontend/dashboard-web") { return "dashboard-web" }
  if ($labelsLower -contains "ws:tooling" -or $labelsLower -contains "workstream/devops" -or $labelsLower -contains "project-hygiene") { return "project-hygiene" }
  if ($labelsLower -contains "testing" -or $labelsLower -contains "qa" -or $labelsLower -contains "test") { return "testing" }

  return $null
}

function Set-ProjectSingleSelectFieldValue {
  param(
    [string]$ItemId,
    [pscustomobject]$Metadata,
    [switch]$DryRun
  )

  if ($DryRun) {
    return
  }

  & $gh.Source project item-edit --id $ItemId --project-id $Metadata.ProjectId --field-id $Metadata.FieldId --single-select-option-id $Metadata.OptionId | Out-Null
  if ($LASTEXITCODE -ne 0) {
    throw "Could not set project field value."
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
  $labels = Get-IssueLabels -IssueNumber $IssueNumber -Repo $Repo
  $priority = Get-ExpectedPriorityOptionName -Labels $labels
  $workstream = Get-ExpectedWorkstreamOptionName -Labels $labels
  if ($priority) { Write-Output "Dry run: would set issue #$IssueNumber Priority to '$priority'." }
  if ($workstream) { Write-Output "Dry run: would set issue #$IssueNumber Workstream to '$workstream'." }
  exit 0
}

Set-ProjectSingleSelectFieldValue -ItemId $item.id -Metadata $metadata

$labels = Get-IssueLabels -IssueNumber $IssueNumber -Repo $Repo
$priority = Get-ExpectedPriorityOptionName -Labels $labels
if ($priority) {
  $priorityMetadata = Get-ProjectSingleSelectMetadata -ProjectNumber $ProjectNumber -ProjectOwner $ProjectOwner -FieldName "Priority" -OptionName $priority
  Set-ProjectSingleSelectFieldValue -ItemId $item.id -Metadata $priorityMetadata
}

$workstream = Get-ExpectedWorkstreamOptionName -Labels $labels
if ($workstream) {
  $workstreamMetadata = Get-ProjectSingleSelectMetadata -ProjectNumber $ProjectNumber -ProjectOwner $ProjectOwner -FieldName "Workstream" -OptionName $workstream
  Set-ProjectSingleSelectFieldValue -ItemId $item.id -Metadata $workstreamMetadata
}

Write-Output "Set issue #$IssueNumber ($($issue.title)) to '$BoardStatus' on project $ProjectOwner/$ProjectNumber."
