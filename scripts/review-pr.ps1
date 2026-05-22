[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [int]$PrNumber,

    [string]$Repo = "robertmccarn/echofinder",
    [string]$BaseBranch = "test-main",
    [string]$WorktreeRoot = "",
    [switch]$SkipCheckout,
    [switch]$DocsOnly,
    [switch]$VerboseReview,
    [string]$OutputMarkdown,
    [switch]$PostComment,
    [switch]$MoveBoard,
    [string]$BoardStatus = "Review",
    [string]$ProjectOwner = "robertmccarn",
    [int]$ProjectNumber = 2,
    [string]$PythonPath = "",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$script:ReportLines = New-Object System.Collections.Generic.List[string]
$script:ValidationRows = New-Object System.Collections.Generic.List[object]
$script:RiskNotes = New-Object System.Collections.Generic.List[string]
$script:ScopeNotes = New-Object System.Collections.Generic.List[string]
$script:BoardRows = New-Object System.Collections.Generic.List[object]
$script:ChecklistRows = New-Object System.Collections.Generic.List[object]

function Add-ReportLine {
    param([string]$Line = "")
    $script:ReportLines.Add($Line)
    Write-Output $Line
}

function Add-Validation {
    param(
        [string]$Command,
        [string]$Status,
        [string]$Details = ""
    )

    $script:ValidationRows.Add([pscustomobject]@{
        Command = $Command
        Status = $Status
        Details = $Details
    })
}

function Resolve-RequiredTool {
    param(
        [string]$Name,
        [string[]]$FallbackPaths = @()
    )

    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    foreach ($path in $FallbackPaths) {
        if (Test-Path $path) {
            return $path
        }
    }

    throw "Required tool '$Name' was not found."
}

# Return a native filesystem path (ProviderPath) for use with external tools like git
function Resolve-NativePath {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not $Path) { return $Path }

    # Resolve the path to a PathInfo object and return the ProviderPath when available
    try {
        $resolved = Resolve-Path -LiteralPath $Path -ErrorAction Stop | Select-Object -First 1
    } catch {
        # If Resolve-Path fails, fall back to the original string
        return $Path
    }

    if ($resolved -and $resolved.Provider -and $resolved.Provider.Name -eq "FileSystem") {
        return $resolved.ProviderPath
    }

    return $resolved.Path
}

function Invoke-Tool {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkingDirectory,
        [string]$DisplayCommand,
        [switch]$AllowFailure
    )

    # Use Start-Process with redirected stdout/stderr to avoid PowerShell
    # converting native stderr into terminating error records. This reliably
    # captures output and exit code from native tools like git/gh.
    $outFile = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), "echofinder-out-$([guid]::NewGuid()).txt")
    $errFile = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), "echofinder-err-$([guid]::NewGuid()).txt")

    $nativeWorkingDirectory = if ($WorkingDirectory) { Resolve-NativePath $WorkingDirectory } else { $null }
    $startInfo = @{ FilePath = $FilePath; WorkingDirectory = $nativeWorkingDirectory; NoNewWindow = $true; RedirectStandardOutput = $outFile; RedirectStandardError = $errFile; Wait = $true; PassThru = $true }
    if ($Arguments -and $Arguments.Count -gt 0) {
        $startInfo.ArgumentList = $Arguments
    }
    try {
        $proc = Start-Process @startInfo
        $exitCode = $proc.ExitCode

        $stdout = if (Test-Path $outFile) { Get-Content -Raw -LiteralPath $outFile } else { "" }
        $stderr = if (Test-Path $errFile) { Get-Content -Raw -LiteralPath $errFile } else { "" }
        $text = (($stdout + "`n" + $stderr).Trim())
    } finally {
        Remove-Item -LiteralPath $outFile -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $errFile -ErrorAction SilentlyContinue
    }

    if ($exitCode -ne 0 -and -not $AllowFailure) {
        throw "Command failed ($exitCode): $DisplayCommand`n$text"
    }

    return [pscustomobject]@{
        ExitCode = $exitCode
        Output = $text
    }
}

function ConvertTo-RepoRelativePath {
    param([string]$Path)
    return ($Path -replace "\\", "/")
}

function Get-FileCategory {
    param([string]$Path)

    $normalized = ConvertTo-RepoRelativePath $Path
    $extension = [System.IO.Path]::GetExtension($normalized).ToLowerInvariant()

    if ($normalized -match '(^|/)(README|CHANGELOG|CONTRIBUTING|LICENSE)(\.md)?$' -or
        $normalized -like "docs/*" -or
        $extension -in @(".md", ".txt", ".pdf")) {
        return "docs"
    }

    if ($normalized -like "backend/*" -or $extension -eq ".py") {
        return "backend/Python"
    }

    if ($normalized -match '(^|/)(package\.json|package-lock\.json|pnpm-lock\.yaml|yarn\.lock|vite\.config|next\.config)' -or
        $normalized -like "frontend/*" -or
        $normalized -like "web/*" -or
        $extension -in @(".js", ".jsx", ".ts", ".tsx", ".css", ".scss")) {
        return "frontend"
    }

    if ($normalized -like ".github/*" -or
        $normalized -match '(^|/)(Dockerfile|docker-compose\.ya?ml|\.gitignore|requirements\.txt|pyproject\.toml|poetry\.lock)$' -or
        $extension -in @(".yml", ".yaml", ".toml", ".ini", ".cfg", ".json")) {
        return "config/devops"
    }

    return "other"
}

function Test-MarkdownLinks {
    param(
        [string[]]$MarkdownFiles,
        [string]$ReviewPath
    )

    $brokenLinks = New-Object System.Collections.Generic.List[string]
    $linkPattern = '\[[^\]]+\]\(([^)]+)\)'

    foreach ($file in $MarkdownFiles) {
        $fullPath = Join-Path $ReviewPath $file
        if (-not (Test-Path $fullPath)) {
            $brokenLinks.Add("$file does not exist")
            continue
        }

        $content = Get-Content -Raw $fullPath
        foreach ($match in [regex]::Matches($content, $linkPattern)) {
            $target = $match.Groups[1].Value.Trim()
            if ($target -match '^(https?:|mailto:|#)' -or $target -eq "") {
                continue
            }

            $targetWithoutAnchor = ($target -split "#")[0]
            if ($targetWithoutAnchor -eq "") {
                continue
            }

            $targetWithoutAnchor = [uri]::UnescapeDataString($targetWithoutAnchor)
            $baseDirectory = Split-Path $fullPath -Parent
            $targetPath = Join-Path $baseDirectory $targetWithoutAnchor
            if (-not (Test-Path $targetPath)) {
                $brokenLinks.Add("$file -> $target")
            }
        }
    }

    return $brokenLinks
}

function Find-ExistingWorktree {
    param(
        [string]$Git,
        [string]$RepoRoot,
        [string]$BranchName
    )

    $nativeRepoRoot = Resolve-NativePath $RepoRoot
    $worktreeOutput = & $Git -C $nativeRepoRoot worktree list --porcelain
    $currentPath = $null

    foreach ($line in $worktreeOutput) {
        if ($line -like "worktree *") {
            $currentPath = $line.Substring("worktree ".Length)
            continue
        }

        if ($line -eq "branch refs/heads/$BranchName") {
            return $currentPath
        }
    }

    return $null
}

function Get-SensitiveScanFindings {
    param(
        [string]$Git,
        [string]$ReviewPath,
        [string]$BaseRef
    )

    $findings = New-Object System.Collections.Generic.List[string]
    $nativeReviewPath = Resolve-NativePath $ReviewPath
    $diff = & $Git -C $nativeReviewPath diff "$BaseRef...HEAD" -- 2>$null
    $currentFile = $null
    $sensitivePattern = '(?i)(\.env|token|api[_-]?key|client[_-]?secret|password|secret)'

    foreach ($line in $diff) {
        if ($line -like "+++ b/*") {
            $currentFile = $line.Substring("+++ b/".Length)
            if ($currentFile -match $sensitivePattern) {
                $findings.Add("$currentFile has a sensitive-looking filename")
            }
            continue
        }

        if ($line.StartsWith("+") -and -not $line.StartsWith("+++")) {
            if ($line -match $sensitivePattern) {
                $fileLabel = if ($currentFile) { $currentFile } else { "unknown file" }
                $findings.Add("$fileLabel has an added line containing a sensitive keyword")
            }
        }
    }

    return $findings | Select-Object -Unique
}

function Get-LinkedIssueNumbers {
    param([object]$PullRequest)

    $issueNumbers = New-Object System.Collections.Generic.List[int]

    if ($PullRequest.closingIssuesReferences) {
        foreach ($issue in $PullRequest.closingIssuesReferences) {
            if ($issue.number) {
                $issueNumbers.Add([int]$issue.number)
            }
        }
    }

    $body = [string]$PullRequest.body
    $keywordPattern = '(?im)^\s*(close[sd]?|fix(e[sd])?|resolve[sd]?)\s+#(\d+)\b'
    foreach ($match in [regex]::Matches($body, $keywordPattern)) {
        $issueNumbers.Add([int]$match.Groups[3].Value)
    }

    return $issueNumbers | Sort-Object -Unique
}

function Get-SectionChecklistItems {
    param(
        [string]$Body,
        [string]$SectionName
    )

    $sectionPattern = '(?is)(?:^|\n)#+\s*' + [regex]::Escape($SectionName) + '\s*(?<section>.*?)(?=\n#+\s|\z)'
    $match = [regex]::Match($Body, $sectionPattern)
    if (-not $match.Success) {
        return @()
    }

    $sectionText = $match.Groups["section"].Value
    $items = New-Object System.Collections.Generic.List[object]
    foreach ($line in ($sectionText -split "`r?`n")) {
        $lineMatch = [regex]::Match($line, '^\s*[-*]\s*\[(?<mark>[xX ])\]\s*(?<text>.+?)\s*$')
        if ($lineMatch.Success) {
            $items.Add([pscustomobject]@{
                Checked = ($lineMatch.Groups["mark"].Value -match '[xX]')
                Text = $lineMatch.Groups["text"].Value.Trim()
            })
        }
    }

    return @($items)
}

function Normalize-IssueBodyText {
    param([string]$Body)
    if (-not $Body) { return "" }
    $normalized = $Body -replace '\\r\\n', "`n"
    $normalized = $normalized -replace '\\n', "`n"
    $normalized = $normalized -replace '\\r', "`n"
    $normalized = $normalized -replace "`r`n", "`n"
    $normalized = $normalized -replace "`r", "`n"
    return $normalized
}

function Add-IssueChecklistAuditRow {
    param(
        [string]$Gh,
        [string]$Repo,
        [int]$IssueNumber
    )

    $issueJson = & $Gh issue view $IssueNumber --repo $Repo --json number,title,body,url
    if ($LASTEXITCODE -ne 0) {
        throw "Could not fetch issue #$IssueNumber for checklist audit."
    }

    $issue = $issueJson | ConvertFrom-Json
    $body = Normalize-IssueBodyText -Body ([string]$issue.body)

    $acItems = @(Get-SectionChecklistItems -Body $body -SectionName "Acceptance Criteria")
    $validationItems = @(Get-SectionChecklistItems -Body $body -SectionName "Validation")

    $acTotal = $acItems.Count
    $acChecked = @($acItems | Where-Object { $_.Checked }).Count
    $validationTotal = $validationItems.Count
    $validationChecked = @($validationItems | Where-Object { $_.Checked }).Count
    $unchecked = @($acItems + $validationItems | Where-Object { -not $_.Checked } | ForEach-Object { $_.Text })

    $script:ChecklistRows.Add([pscustomobject]@{
        Issue = "#$IssueNumber"
        Title = $issue.title
        Url = $issue.url
        AcChecked = $acChecked
        AcTotal = $acTotal
        ValidationChecked = $validationChecked
        ValidationTotal = $validationTotal
        UncheckedItems = $unchecked
        MissingChecklist = (($acTotal + $validationTotal) -eq 0)
    })
}

function Get-ProjectStatusMetadata {
    param(
        [string]$Gh,
        [int]$ProjectNumber,
        [string]$ProjectOwner,
        [string]$StatusName
    )

    $query = 'query($login:String!,$field:String!){ user(login:$login){ projectV2(number:' + $ProjectNumber + '){ id field(name:$field){ __typename ... on ProjectV2SingleSelectField{ id name options{ id name } } } } } }'
    $fieldsJson = & $Gh api graphql -f "query=$query" -f "login=$ProjectOwner" -f "field=Status"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not fetch project Status field for $ProjectOwner/$ProjectNumber."
    }

    $project = ($fieldsJson | ConvertFrom-Json).data.user.projectV2
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
        FieldId = $statusField.id
        OptionId = $statusOption.id
    }
}

function Get-ProjectSingleSelectFieldMetadata {
    param(
        [string]$Gh,
        [int]$ProjectNumber,
        [string]$ProjectOwner,
        [string]$FieldName,
        [string]$OptionName
    )

    $query = 'query($login:String!,$field:String!){ user(login:$login){ projectV2(number:' + $ProjectNumber + '){ id field(name:$field){ __typename ... on ProjectV2SingleSelectField{ id name options{ id name } } } } } }'
    $fieldsJson = & $Gh api graphql -f "query=$query" -f "login=$ProjectOwner" -f "field=$FieldName"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not fetch project field '$FieldName' for $ProjectOwner/$ProjectNumber."
    }

    $project = ($fieldsJson | ConvertFrom-Json).data.user.projectV2
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
        FieldId = $field.id
        OptionId = $option.id
    }
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

function Set-ProjectSingleSelectField {
    param(
        [string]$Gh,
        [string]$ItemId,
        [string]$ProjectId,
        [string]$FieldId,
        [string]$OptionId
    )

    & $Gh project item-edit --id $ItemId --project-id $ProjectId --field-id $FieldId --single-select-option-id $OptionId | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Could not update project field."
    }
}

function Get-ProjectId {
    param(
        [string]$Gh,
        [int]$ProjectNumber,
        [string]$ProjectOwner
    )

    $query = 'query($login:String!){ user(login:$login){ projectV2(number:' + $ProjectNumber + '){ id } } }'
    $projectJson = & $Gh api graphql -f "query=$query" -f "login=$ProjectOwner"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not fetch project $ProjectOwner/$ProjectNumber."
    }

    $project = ($projectJson | ConvertFrom-Json).data.user.projectV2
    if (-not $project) {
        throw "Project $ProjectOwner/$ProjectNumber was not found."
    }

    return $project.id
}

function Get-ProjectItemForIssue {
    param(
        [string]$Gh,
        [int]$ProjectNumber,
        [string]$ProjectOwner,
        [int]$IssueNumber
    )

    $query = 'query($login:String!){ user(login:$login){ projectV2(number:' + $ProjectNumber + '){ items(first:100){ nodes{ id content{ __typename ... on Issue{ number } } } } } } }'
    $itemsJson = & $Gh api graphql -f "query=$query" -f "login=$ProjectOwner"
    if ($LASTEXITCODE -ne 0) {
        throw "Could not fetch project items for $ProjectOwner/$ProjectNumber."
    }

    $items = ($itemsJson | ConvertFrom-Json).data.user.projectV2.items.nodes
    return $items | Where-Object { $_.content.__typename -eq "Issue" -and $_.content.number -eq $IssueNumber } | Select-Object -First 1
}

function Update-BoardStatusForIssue {
    param(
        [string]$Gh,
        [string]$Repo,
        [int]$IssueNumber,
        [int]$ProjectNumber,
        [string]$ProjectOwner,
        [string]$BoardStatus,
        [switch]$MoveBoard,
        [switch]$DryRun
    )

    $issueJson = & $Gh issue view $IssueNumber --repo $Repo --json number,title,url,labels
    if ($LASTEXITCODE -ne 0) {
        throw "Could not fetch issue #$IssueNumber."
    }
    $issue = $issueJson | ConvertFrom-Json

    $action = if ($MoveBoard) { "UPDATE" } else { "PLAN" }
    $details = "Would set Status to '$BoardStatus'."

    if ($MoveBoard) {
        $projectId = Get-ProjectId -Gh $Gh -ProjectNumber $ProjectNumber -ProjectOwner $ProjectOwner
        $metadata = Get-ProjectStatusMetadata -Gh $Gh -ProjectNumber $ProjectNumber -ProjectOwner $ProjectOwner -StatusName $BoardStatus
        $item = Get-ProjectItemForIssue -Gh $Gh -ProjectNumber $ProjectNumber -ProjectOwner $ProjectOwner -IssueNumber $IssueNumber

        if (-not $item) {
            if ($DryRun) {
                $details = "Dry run: would add issue to project and set Status to '$BoardStatus'."
            } else {
                $addJson = & $Gh project item-add $ProjectNumber --owner $ProjectOwner --url $issue.url --format json
                if ($LASTEXITCODE -ne 0) {
                    throw "Could not add issue #$IssueNumber to project $ProjectOwner/$ProjectNumber."
                }

                $item = $addJson | ConvertFrom-Json
                $details = "Added issue to project and set Status to '$BoardStatus'."
            }
        } else {
            $details = if ($DryRun) { "Dry run: would set Status to '$BoardStatus'." } else { "Set Status to '$BoardStatus'." }
        }

        if (-not $DryRun) {
            Set-ProjectSingleSelectField -Gh $Gh -ItemId $item.id -ProjectId $projectId -FieldId $metadata.FieldId -OptionId $metadata.OptionId

            $labels = @($issue.labels | ForEach-Object { [string]$_.name })
            $priorityOption = Get-ExpectedPriorityOptionName -Labels $labels
            if ($priorityOption) {
                $priorityMetadata = Get-ProjectSingleSelectFieldMetadata -Gh $Gh -ProjectNumber $ProjectNumber -ProjectOwner $ProjectOwner -FieldName "Priority" -OptionName $priorityOption
                Set-ProjectSingleSelectField -Gh $Gh -ItemId $item.id -ProjectId $projectId -FieldId $priorityMetadata.FieldId -OptionId $priorityMetadata.OptionId
            }

            $workstreamOption = Get-ExpectedWorkstreamOptionName -Labels $labels
            if ($workstreamOption) {
                $workstreamMetadata = Get-ProjectSingleSelectFieldMetadata -Gh $Gh -ProjectNumber $ProjectNumber -ProjectOwner $ProjectOwner -FieldName "Workstream" -OptionName $workstreamOption
                Set-ProjectSingleSelectField -Gh $Gh -ItemId $item.id -ProjectId $projectId -FieldId $workstreamMetadata.FieldId -OptionId $workstreamMetadata.OptionId
            }
        }
    }

    $script:BoardRows.Add([pscustomobject]@{
        Issue = "#$IssueNumber"
        Title = $issue.title
        Project = "$ProjectOwner/$ProjectNumber"
        TargetStatus = $BoardStatus
        Action = $action
        Details = $details
    })
}

$repoRoot = Resolve-NativePath (Join-Path $PSScriptRoot "..")
if ($WorktreeRoot -and ((Resolve-NativePath $WorktreeRoot) -ne $repoRoot)) {
    throw "WorktreeRoot is no longer supported. Run review-pr.ps1 from the canonical EchoFinder repository root only: $repoRoot"
}
$git = Resolve-RequiredTool -Name "git" -FallbackPaths @(
    "C:\Program Files\Git\cmd\git.exe",
    "C:\Program Files\Git\bin\git.exe",
    "C:\Program Files\Git\mingw64\bin\git.exe"
)
$gh = Resolve-RequiredTool -Name "gh" -FallbackPaths @(
    "C:\Tools\gh\gh.exe",
    "C:\Program Files\GitHub CLI\gh.exe"
)
$python = $null
if ($PythonPath) {
    if (-not (Test-Path -LiteralPath $PythonPath)) {
        throw "Provided -PythonPath does not exist: $PythonPath"
    }
    $python = Resolve-NativePath $PythonPath
} else {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        $python = $pythonCommand.Source
    }
}

Invoke-Tool -FilePath $git -Arguments @("--version") -WorkingDirectory $repoRoot -DisplayCommand "git --version" | Out-Null
Invoke-Tool -FilePath $gh -Arguments @("--version") -WorkingDirectory $repoRoot -DisplayCommand "gh --version" | Out-Null

$authResult = Invoke-Tool -FilePath $gh -Arguments @("auth", "status") -WorkingDirectory $repoRoot -DisplayCommand "gh auth status" -AllowFailure
if ($authResult.ExitCode -eq 0) {
    Add-Validation -Command "gh auth status" -Status "PASS" -Details "Authenticated; token details intentionally not logged."
} else {
    Add-Validation -Command "gh auth status" -Status "FAIL" -Details "GitHub CLI is not authenticated."
}

$jsonFields = "number,title,body,baseRefName,headRefName,state,isDraft,mergeable,changedFiles,url,author,closingIssuesReferences"
$prJson = & $gh pr view $PrNumber --repo $Repo --json $jsonFields
if ($LASTEXITCODE -ne 0) {
    throw "Could not fetch PR #$PrNumber metadata."
}
$pr = $prJson | ConvertFrom-Json

if ($pr.baseRefName -ne $BaseBranch) {
    $script:RiskNotes.Add("PR base branch is '$($pr.baseRefName)', expected '$BaseBranch'.")
}

$remoteBaseRef = "origin/$BaseBranch"
& $git -C (Resolve-NativePath $repoRoot) rev-parse --verify --quiet $remoteBaseRef | Out-Null
$baseCompareRef = if ($LASTEXITCODE -eq 0) { $remoteBaseRef } else { $BaseBranch }

$reviewPath = $repoRoot

$changedFiles = @(& $gh pr diff $PrNumber --repo $Repo --name-only)
if ($LASTEXITCODE -ne 0) {
    throw "Could not fetch changed file list for PR #$PrNumber."
}

$groupedFiles = $changedFiles | ForEach-Object {
    [pscustomobject]@{
        Path = $_
        Category = Get-FileCategory $_
    }
} | Group-Object Category

$categories = @($groupedFiles | ForEach-Object { $_.Name })
$classification = if ($DocsOnly -or ($categories.Count -eq 1 -and $categories[0] -eq "docs")) {
    "docs-only"
} elseif ($categories.Count -eq 1) {
    $categories[0]
} else {
    "mixed"
}

$statusResult = Invoke-Tool -FilePath $git -Arguments @("-C", $reviewPath, "status", "--short") -WorkingDirectory $reviewPath -DisplayCommand "git status --short" -AllowFailure
Add-Validation -Command "git status --short" -Status ($(if ($statusResult.ExitCode -eq 0) { "PASS" } else { "FAIL" })) -Details ($(if ($statusResult.Output) { "Output present; inspect manually." } else { "Clean working tree." }))

$diffCheckResult = Invoke-Tool -FilePath $git -Arguments @("-C", $reviewPath, "diff", "--check") -WorkingDirectory $reviewPath -DisplayCommand "git diff --check" -AllowFailure
Add-Validation -Command "git diff --check" -Status ($(if ($diffCheckResult.ExitCode -eq 0) { "PASS" } else { "FAIL" })) -Details ($(if ($diffCheckResult.Output) { $diffCheckResult.Output } else { "No whitespace errors." }))

$rangeDiffCheckResult = Invoke-Tool -FilePath $git -Arguments @("-C", $reviewPath, "diff", "--check", "$baseCompareRef...HEAD") -WorkingDirectory $reviewPath -DisplayCommand "git diff --check $baseCompareRef...HEAD" -AllowFailure
Add-Validation -Command "git diff --check $baseCompareRef...HEAD" -Status ($(if ($rangeDiffCheckResult.ExitCode -eq 0) { "PASS" } else { "FAIL" })) -Details ($(if ($rangeDiffCheckResult.Output) { $rangeDiffCheckResult.Output } else { "No whitespace errors in PR diff." }))

$markdownFiles = @($changedFiles | Where-Object { [System.IO.Path]::GetExtension($_).ToLowerInvariant() -eq ".md" })
if ($classification -eq "docs-only" -or $markdownFiles.Count -gt 0) {
    $missingMarkdown = @($markdownFiles | Where-Object { -not (Test-Path (Join-Path $reviewPath $_)) })
    if ($missingMarkdown.Count -eq 0) {
        Add-Validation -Command "Confirm changed Markdown files exist" -Status "PASS" -Details "$($markdownFiles.Count) Markdown file(s) checked."
    } else {
        Add-Validation -Command "Confirm changed Markdown files exist" -Status "FAIL" -Details ($missingMarkdown -join ", ")
    }

    $brokenLinks = @(Test-MarkdownLinks -MarkdownFiles $markdownFiles -ReviewPath $reviewPath)
    if ($brokenLinks.Count -eq 0) {
        Add-Validation -Command "Check local Markdown links" -Status "PASS" -Details "No obviously broken local links found in changed Markdown files."
    } else {
        Add-Validation -Command "Check local Markdown links" -Status "FAIL" -Details ($brokenLinks -join "; ")
    }
}

if ($categories -contains "backend/Python") {
    if ($python) {
        $compileResult = Invoke-Tool -FilePath $python -Arguments @("-m", "compileall", "backend") -WorkingDirectory $reviewPath -DisplayCommand "python -m compileall backend" -AllowFailure
        Add-Validation -Command "python -m compileall backend" -Status ($(if ($compileResult.ExitCode -eq 0) { "PASS" } else { "FAIL" })) -Details ($(if ($compileResult.ExitCode -eq 0) { "Python files compiled." } else { $compileResult.Output }))
    } else {
        Add-Validation -Command "python -m compileall backend" -Status "SKIP" -Details "Skipped because Python executable was not found. Pass -PythonPath to review-pr.ps1 to enable backend validation."
    }

    $pytestFiles = Get-ChildItem -Path $reviewPath -Recurse -Include "test_*.py", "*_test.py" -ErrorAction SilentlyContinue
    if ($pytestFiles) {
        $pytest = Get-Command pytest -ErrorAction SilentlyContinue
        if ($pytest) {
            $pytestResult = Invoke-Tool -FilePath $pytest.Source -Arguments @() -WorkingDirectory $reviewPath -DisplayCommand "pytest" -AllowFailure
            Add-Validation -Command "pytest" -Status ($(if ($pytestResult.ExitCode -eq 0) { "PASS" } else { "FAIL" })) -Details $pytestResult.Output
        } else {
            Add-Validation -Command "pytest" -Status "SKIP" -Details "Python tests exist, but pytest is not available."
        }
    } else {
        Add-Validation -Command "pytest" -Status "SKIP" -Details "No pytest-style tests found."
    }
} else {
    Add-Validation -Command "python -m compileall backend" -Status "SKIP" -Details "Skipped because no backend/Python files changed."
}

if ($categories -contains "frontend") {
    $lockfiles = @("pnpm-lock.yaml", "yarn.lock", "package-lock.json", "package.json") | Where-Object { Test-Path (Join-Path $reviewPath $_) }
    if ($lockfiles.Count -eq 0) {
        Add-Validation -Command "frontend validation" -Status "SKIP" -Details "Frontend files changed, but no package manager lockfile/package.json was found."
    } else {
        Add-Validation -Command "frontend validation" -Status "SKIP" -Details "Frontend validation requires project-documented commands before running install/test/lint."
    }
}

$sensitiveFindings = @(Get-SensitiveScanFindings -Git $git -ReviewPath $reviewPath -BaseRef $baseCompareRef)
if ($sensitiveFindings.Count -gt 0) {
    foreach ($finding in $sensitiveFindings) {
        $script:RiskNotes.Add("Sensitive-content scan: $finding. Value intentionally not printed.")
    }
}

$titleAndBody = "$($pr.title)`n$($pr.body)"
if ($classification -eq "docs-only" -and ($categories | Where-Object { $_ -ne "docs" }).Count -gt 0) {
    $script:ScopeNotes.Add("Possible scope creep: docs-only PR includes non-doc changes.")
}
$automationScoped = $titleAndBody -match '(?i)automation|tooling|script|lifecycle|project board'
if ($titleAndBody -match '(?i)docs|documentation|workflow' -and -not $automationScoped -and ($categories | Where-Object { $_ -notin @("docs") }).Count -gt 0) {
    $script:ScopeNotes.Add("Possible scope creep: documentation-themed PR includes non-doc categories.")
}
if (($categories -contains "config/devops") -and $titleAndBody -notmatch '(?i)config|ci|devops|workflow|dependency') {
    $script:ScopeNotes.Add("Config/devops files changed without an obvious mention in title/body.")
}
if ($changedFiles | Where-Object { $_ -match '(^|/)\.env($|\.|/)|secret|credential|token' }) {
    $script:ScopeNotes.Add("Sensitive-looking file path changed; inspect manually.")
}
if ($script:ScopeNotes.Count -eq 0) {
    $script:ScopeNotes.Add("In-scope based on changed files and PR title/body.")
}

$linkedIssues = @(Get-LinkedIssueNumbers -PullRequest $pr)
if ($linkedIssues.Count -gt 0) {
    foreach ($issueNumber in $linkedIssues) {
        Add-IssueChecklistAuditRow -Gh $gh -Repo $Repo -IssueNumber $issueNumber
    }

    $hasUnchecked = @($script:ChecklistRows | Where-Object {
        (($_.AcTotal -gt 0 -and $_.AcChecked -lt $_.AcTotal) -or ($_.ValidationTotal -gt 0 -and $_.ValidationChecked -lt $_.ValidationTotal))
    })
    $missingChecklist = @($script:ChecklistRows | Where-Object { $_.MissingChecklist })

    if ($hasUnchecked.Count -gt 0) {
        Add-Validation -Command "Issue checklist audit (AC/Validation)" -Status "FAIL" -Details "Unchecked checklist items remain on linked issue(s): $((@($hasUnchecked | ForEach-Object { $_.Issue }) -join ', '))."
    } elseif ($missingChecklist.Count -gt 0) {
        Add-Validation -Command "Issue checklist audit (AC/Validation)" -Status "FAIL" -Details "No checklist items found in Acceptance Criteria/Validation for linked issue(s): $((@($missingChecklist | ForEach-Object { $_.Issue }) -join ', '))."
    } else {
        Add-Validation -Command "Issue checklist audit (AC/Validation)" -Status "PASS" -Details "All linked issue Acceptance Criteria and Validation checklist items are checked."
    }
}

$failedValidation = @($script:ValidationRows | Where-Object { $_.Status -eq "FAIL" })
$recommendation = if ($failedValidation.Count -gt 0 -or $sensitiveFindings.Count -gt 0) {
    "REQUEST_CHANGES"
} elseif ($pr.isDraft -or $script:RiskNotes.Count -gt 0 -or ($script:ScopeNotes | Where-Object { $_ -like "Possible scope creep*" }).Count -gt 0) {
    "NEEDS_MANUAL_REVIEW"
} else {
    "APPROVE_READY"
}

if ($linkedIssues.Count -eq 0) {
    $script:BoardRows.Add([pscustomobject]@{
        Issue = "-"
        Title = "-"
        Project = "$ProjectOwner/$ProjectNumber"
        TargetStatus = $BoardStatus
        Action = "SKIP"
        Details = "No linked issues found from GitHub closing references or PR body keywords."
    })
} elseif ($recommendation -eq "REQUEST_CHANGES" -and $MoveBoard) {
    foreach ($issueNumber in $linkedIssues) {
        $script:BoardRows.Add([pscustomobject]@{
            Issue = "#$issueNumber"
            Title = "-"
            Project = "$ProjectOwner/$ProjectNumber"
            TargetStatus = $BoardStatus
            Action = "SKIP"
            Details = "Board move skipped because recommendation is REQUEST_CHANGES."
        })
    }
} else {
    foreach ($issueNumber in $linkedIssues) {
        Update-BoardStatusForIssue -Gh $gh -Repo $Repo -IssueNumber $issueNumber -ProjectNumber $ProjectNumber -ProjectOwner $ProjectOwner -BoardStatus $BoardStatus -MoveBoard:$MoveBoard -DryRun:$DryRun
    }
}

Add-ReportLine "## PR Summary"
Add-ReportLine "- PR: #$($pr.number) $($pr.title)"
Add-ReportLine "- URL: $($pr.url)"
Add-ReportLine "- Base/head: $($pr.baseRefName) <- $($pr.headRefName)"
Add-ReportLine "- State: $($pr.state); Draft: $($pr.isDraft)"
Add-ReportLine "- Changed file count: $($changedFiles.Count)"
Add-ReportLine "- Classification: $classification"
Add-ReportLine "- Review path: $reviewPath"
Add-ReportLine ""

Add-ReportLine "## Changed Files"
foreach ($group in ($groupedFiles | Sort-Object Name)) {
    Add-ReportLine "### $($group.Name)"
    foreach ($file in ($group.Group | Sort-Object Path)) {
        Add-ReportLine "- $($file.Path)"
    }
}
Add-ReportLine ""

Add-ReportLine "## Validation"
foreach ($row in $script:ValidationRows) {
    $details = if ($row.Details) { " - $($row.Details)" } else { "" }
    Add-ReportLine "- $($row.Status): ``$($row.Command)``$details"
}
Add-ReportLine ""

Add-ReportLine "## Scope Review"
foreach ($note in $script:ScopeNotes) {
    Add-ReportLine "- $note"
}
Add-ReportLine ""

Add-ReportLine "## Risk Notes"
if ($script:RiskNotes.Count -eq 0) {
    Add-ReportLine "- No automated risk notes found."
} else {
    foreach ($note in $script:RiskNotes) {
        Add-ReportLine "- $note"
    }
}
Add-ReportLine ""

Add-ReportLine "## Checklist Audit"
if ($script:ChecklistRows.Count -eq 0) {
    Add-ReportLine "- No linked issues to audit."
} else {
    foreach ($row in $script:ChecklistRows) {
        Add-ReportLine "- $($row.Issue): AC $($row.AcChecked)/$($row.AcTotal), Validation $($row.ValidationChecked)/$($row.ValidationTotal)"
        if ($row.UncheckedItems.Count -gt 0) {
            foreach ($item in $row.UncheckedItems) {
                Add-ReportLine "  - [ ] $item"
            }
        }
    }
}
Add-ReportLine ""

Add-ReportLine "## Board Movement"
foreach ($row in $script:BoardRows) {
    Add-ReportLine "- $($row.Action): $($row.Issue) -> $($row.TargetStatus) on project $($row.Project) - $($row.Details)"
}
Add-ReportLine ""

Add-ReportLine "## Recommendation"
Add-ReportLine $recommendation

if ($OutputMarkdown) {
    $outputDirectory = Split-Path $OutputMarkdown -Parent
    if ($outputDirectory -and -not (Test-Path $outputDirectory)) {
        New-Item -ItemType Directory -Path $outputDirectory | Out-Null
    }
    $script:ReportLines | Set-Content -Path $OutputMarkdown -Encoding utf8
}

if ($PostComment) {
    $commentPath = if ($OutputMarkdown) {
        $OutputMarkdown
    } else {
        $temporaryPath = Join-Path ([System.IO.Path]::GetTempPath()) "echofinder-pr-$PrNumber-review.md"
        $script:ReportLines | Set-Content -Path $temporaryPath -Encoding utf8
        $temporaryPath
    }

    Invoke-Tool -FilePath $gh -Arguments @("pr", "comment", "$PrNumber", "--repo", $Repo, "--body-file", $commentPath) -WorkingDirectory $reviewPath -DisplayCommand "gh pr comment $PrNumber --repo $Repo --body-file <report>" | Out-Null
}
