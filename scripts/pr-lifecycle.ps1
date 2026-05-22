[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [int]$PrNumber,

    [string]$Repo = "robertmccarn/echofinder",
    [string]$BaseBranch = "test-main",
    [string]$WorktreeRoot = "",
    [switch]$AutoApprove,
    [switch]$AllowSelfApproval,
    [switch]$AllowManualReviewApprove,
    [switch]$AutoMerge,
    [switch]$AllowManualReviewMerge,
    [switch]$ValidateAfterMerge,
    [switch]$MoveBoard,
    [string]$BoardStatus = "Pending Release",
    [string]$ProjectOwner = "robertmccarn",
    [int]$ProjectNumber = 2,
    [switch]$PostComment,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

if ($BaseBranch -eq "main") {
    throw "BaseBranch cannot be 'main'. Releases to main must be handled manually or via a dedicated release workflow."
}

$script:LifecycleSummary = New-Object System.Collections.Generic.List[string]
$script:QaResult = "UNKNOWN"
$script:ReviewStatus = "SKIPPED"
$script:MergeStatus = "SKIPPED"
$script:PostMergeValidation = "SKIPPED"
$script:BoardMovementStatus = "SKIPPED"
$script:OverrideNotes = New-Object System.Collections.Generic.List[string]
$script:LinkedIssues = New-Object System.Collections.Generic.List[int]

function Add-Summary {
    param([string]$Line = "")
    $script:LifecycleSummary.Add($Line)
    Write-Output $Line
}

function Resolve-RequiredTool {
    param([string]$Name)
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    throw "Required tool '$Name' was not found."
}

function Get-LinkedIssueNumbersFromPr {
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

    return @($issueNumbers | Sort-Object -Unique)
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

    return @($items.ToArray())
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

function Post-IssueChecklistQaComments {
    param(
        [string]$Gh,
        [string]$Repo,
        [int[]]$IssueNumbers,
        [string]$QaResult,
        [switch]$DryRun
    )

    foreach ($issueNumber in $IssueNumbers) {
        $issueJson = & $Gh issue view $issueNumber --repo $Repo --json number,title,body
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Could not fetch issue #$issueNumber for QA checklist comment."
            continue
        }

        $issue = $issueJson | ConvertFrom-Json
        $issueBody = Normalize-IssueBodyText -Body ([string]$issue.body)
        $acItems = @(Get-SectionChecklistItems -Body $issueBody -SectionName "Acceptance Criteria")
        $validationItems = @(Get-SectionChecklistItems -Body $issueBody -SectionName "Validation")
        $unchecked = @($acItems + $validationItems | Where-Object { -not $_.Checked } | ForEach-Object { $_.Text })

        $comment = @"
QA Checklist Audit (from PR #$PrNumber)

Result: $QaResult
- Acceptance Criteria checked: $(@($acItems | Where-Object { $_.Checked }).Count)/$($acItems.Count)
- Validation checked: $(@($validationItems | Where-Object { $_.Checked }).Count)/$($validationItems.Count)
"@
        if ($unchecked.Count -gt 0) {
            $comment += "`nUnchecked items:`n- " + ($unchecked -join "`n- ")
        } else {
            $comment += "`nAll checklist items are checked."
        }

        if ($DryRun) {
            Write-Host "Dry Run: Would post checklist QA comment to issue #$issueNumber"
        } else {
            & $Gh issue comment $issueNumber --repo $Repo --body $comment | Out-Null
        }
    }
}

$git = Resolve-RequiredTool -Name "git"
$gh = Resolve-RequiredTool -Name "gh"
$python = Resolve-RequiredTool -Name "python"

$repoRoot = Split-Path -Parent $PSScriptRoot
if ($WorktreeRoot -and ((Resolve-Path -LiteralPath $WorktreeRoot).ProviderPath -ne (Resolve-Path -LiteralPath $repoRoot).ProviderPath)) {
    throw "WorktreeRoot is no longer supported. Run pr-lifecycle.ps1 from the canonical EchoFinder repository root only: $repoRoot"
}
$WorktreeRoot = $repoRoot

# --- Metadata Retrieval ---
Write-Host "### Fetching PR Metadata" -ForegroundColor Cyan
$prJson = & $gh pr view $PrNumber --repo $Repo --json author,isDraft,mergeable,baseRefName,reviews,body,closingIssuesReferences
$pr = $prJson | ConvertFrom-Json
$script:LinkedIssues = @(Get-LinkedIssueNumbersFromPr -PullRequest $pr)

if ($pr.baseRefName -ne $BaseBranch) {
    throw "PR base branch is '$($pr.baseRefName)', but expected '$BaseBranch'. Aborting for safety."
}

if ($pr.isDraft) {
    throw "PR #$PrNumber is a draft. Aborting for safety."
}

# --- Phase 1: QA ---
Write-Host "`n### Phase 1: QA" -ForegroundColor Cyan
$reviewScript = Join-Path $PSScriptRoot "review-pr.ps1"
$tempReport = [System.IO.Path]::GetTempFileName()

    $reviewArgs = @(
        "-PrNumber", $PrNumber,
        "-Repo", $Repo,
        "-BaseBranch", $BaseBranch,
        "-WorktreeRoot", $WorktreeRoot,
        "-OutputMarkdown", $tempReport
    )

    # When running a dry-run from an environment that may have local changes, avoid attempting a gh checkout
    # Also propagate the DryRun flag so review-pr.ps1 can treat SkipCheckout as non-risk when appropriate.
    if ($DryRun) {
        $reviewArgs += "-SkipCheckout"
        $reviewArgs += "-DryRun"
    }

try {
    # Run the existing review script
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $reviewScript @reviewArgs

    # Capture the last standalone recommendation line (APPROVE_READY, NEEDS_MANUAL_REVIEW, REQUEST_CHANGES)
    # Use a multiline regex to find all lines that consist solely of a recommendation and pick the last one.
    $reportContent = Get-Content $tempReport -Raw
    $recommendationMatches = [regex]::Matches(
        $reportContent,
        "(?m)^\s*(APPROVE_READY|NEEDS_MANUAL_REVIEW|REQUEST_CHANGES)\s*$"
    )

    if ($recommendationMatches.Count -gt 0) {
        $script:QaResult = $recommendationMatches[$recommendationMatches.Count - 1].Groups[1].Value
    }
} finally {
    if (Test-Path $tempReport) { Remove-Item $tempReport }
}

Write-Host "QA Recommendation: $script:QaResult" -ForegroundColor Yellow

if ($script:LinkedIssues.Count -gt 0) {
    Post-IssueChecklistQaComments -Gh $gh -Repo $Repo -IssueNumbers $script:LinkedIssues -QaResult $script:QaResult -DryRun:$DryRun
}

# --- Phase 2: Review ---
Write-Host "`n### Phase 2: Review" -ForegroundColor Cyan
$canApprove = ($script:QaResult -eq "APPROVE_READY") -or ($script:QaResult -eq "NEEDS_MANUAL_REVIEW" -and $AllowManualReviewApprove)

if ($script:QaResult -eq "NEEDS_MANUAL_REVIEW" -and $AllowManualReviewApprove) {
    $script:OverrideNotes.Add("Manual review approval override was used.")
}

# Check for existing APPROVED reviews
$existingApprovals = $pr.reviews | Where-Object { $_.state -eq "APPROVED" }
if ($existingApprovals) {
    $script:ReviewStatus = "ALREADY APPROVED"
    Write-Host "Existing approval(s) found: $(($existingApprovals | ForEach-Object { $_.author.login }) -join ', ')"
}

if ($AutoApprove) {
    if ($canApprove) {
        $currentUser = (& $gh api user --jq .login)
        $isAuthor = ($pr.author.login -eq $currentUser)

        if ($isAuthor -and -not $AllowSelfApproval) {
            $script:ReviewStatus = "BLOCKED (Author requires -AllowSelfApproval)"
            Write-Warning "You are the author of PR #$PrNumber. Approval requires -AllowSelfApproval."
        } elseif ($DryRun) {
            $script:ReviewStatus = "PLAN (Dry Run)"
            Write-Host "Dry Run: Would approve PR #$PrNumber"
        } else {
            $approveMsg = "Automated approval based on QA result: $script:QaResult"
            $previousErrorActionPreference = $ErrorActionPreference
            $ErrorActionPreference = "Continue"
            $approveResult = & $gh pr review $PrNumber --repo $Repo --approve --body $approveMsg 2>&1
            $ErrorActionPreference = $previousErrorActionPreference
            if ($LASTEXITCODE -eq 0) {
                $script:ReviewStatus = "APPROVED"
                Write-Host "PR #$PrNumber approved."
            } else {
                if ($approveResult -match "Can not approve your own pull request") {
                    if ($AllowSelfApproval) {
                        $script:ReviewStatus = "SELF-APPROVED (Validated)"
                        Write-Host "Self-approval noted and allowed via flag."
                    } else {
                        $script:ReviewStatus = "BLOCKED (GitHub API restriction)"
                        Write-Warning "GitHub API blocked self-approval. Use -AllowSelfApproval to proceed with merge."
                    }
                } else {
                    $script:ReviewStatus = "FAILED"
                    Write-Error "Approval failed: $approveResult"
                }
            }
        }
    } else {
        $script:ReviewStatus = "BLOCKED (QA status: $script:QaResult)"
        Write-Warning "Cannot auto-approve. QA result is $script:QaResult."
    }
}

# --- Phase 3: Merge ---
Write-Host "`n### Phase 3: Merge" -ForegroundColor Cyan
$isApproved = ($script:ReviewStatus -in @("APPROVED", "SELF-APPROVED (Validated)", "ALREADY APPROVED"))
$canMerge = ($script:QaResult -eq "APPROVE_READY") -or ($script:QaResult -eq "NEEDS_MANUAL_REVIEW" -and $AllowManualReviewMerge)

if ($script:QaResult -eq "NEEDS_MANUAL_REVIEW" -and $AllowManualReviewMerge) {
    $script:OverrideNotes.Add("Manual review merge override was used.")
}

if ($AutoMerge) {
    if ($canMerge -and $isApproved) {
        if ($pr.mergeable -and $pr.mergeable -notin @("MERGEABLE", "UNKNOWN")) {
            $script:MergeStatus = "BLOCKED (Not mergeable: $($pr.mergeable))"
            Write-Warning "PR is not mergeable: $($pr.mergeable)"
        } elseif ($DryRun) {
            $script:MergeStatus = "PLAN (Dry Run)"
            Write-Host "Dry Run: Would squash-merge PR #$PrNumber into $BaseBranch"
        } else {
            $mergeResult = & $gh pr merge $PrNumber --repo $Repo --squash --delete-branch 2>&1
            if ($LASTEXITCODE -eq 0) {
                $script:MergeStatus = "MERGED TO $BaseBranch"
                Write-Host "PR #$PrNumber merged."
            } else {
                $script:MergeStatus = "FAILED"
                Write-Error "Merge failed: $mergeResult"
            }
        }
    } else {
        $script:MergeStatus = "BLOCKED (Approval missing or QA unsafe)"
        Write-Warning "Cannot auto-merge. Approval status: $script:ReviewStatus. QA result: $script:QaResult. AllowManualReviewMerge: $AllowManualReviewMerge"
    }
}

# --- Phase 4: Post-merge Validation ---
if ($script:MergeStatus -eq "MERGED TO $BaseBranch" -and $ValidateAfterMerge) {
    Write-Host "`n### Phase 4: Post-merge Validation" -ForegroundColor Cyan
    if ($DryRun) {
        $script:PostMergeValidation = "PLAN (Dry Run)"
    } else {
        $repoPath = $WorktreeRoot
        Push-Location $repoPath
        try {
            Write-Host "Updating local $BaseBranch..."
            & $git checkout $BaseBranch
            & $git pull origin $BaseBranch

            Write-Host "Running post-merge checks..."
            & $git status --short
            & $git diff --check
            & $python -m compileall backend

            $pytest = Get-Command pytest -ErrorAction SilentlyContinue
            if ($pytest) {
                $pytestFiles = Get-ChildItem -Path $repoPath -Recurse -Include "test_*.py", "*_test.py" -ErrorAction SilentlyContinue
                if ($pytestFiles) {
                    Write-Host "Running pytest..."
                    & $pytest
                } else {
                    Write-Host "Skipping pytest because no pytest-style tests were found."
                }
            }

            if ($LASTEXITCODE -eq 0) {
                $script:PostMergeValidation = "PASS"
                Write-Host "Post-merge validation passed."
            } else {
                $script:PostMergeValidation = "FAILED"
                Write-Error "Post-merge validation failed."
            }
        } finally {
            Pop-Location
        }
    }
}

# --- Phase 5: Board Movement ---
$shouldMove = $MoveBoard -and ($script:MergeStatus -match "MERGED" -or $DryRun)
if ($ValidateAfterMerge -and $script:PostMergeValidation -eq "FAILED") {
    Write-Warning "Post-merge validation failed. Skipping board movement."
    $shouldMove = $false
}

if ($shouldMove) {
    Write-Host "`n### Phase 5: Board Movement" -ForegroundColor Cyan
    $moveScript = $reviewScript

    $moveArgs = @(
        "-PrNumber", $PrNumber,
        "-Repo", $Repo,
        "-MoveBoard",
        "-BoardStatus", $BoardStatus,
        "-ProjectOwner", $ProjectOwner,
        "-ProjectNumber", $ProjectNumber,
        "-SkipCheckout"
    )
    if ($DryRun) { $moveArgs += "-DryRun" }

    try {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $moveScript @moveArgs
        $script:BoardMovementStatus = if ($DryRun) { "PLAN (Dry Run)" } else { $BoardStatus }
    } catch {
        $script:BoardMovementStatus = "FAILED"
        Write-Error "Board movement failed: $_"
    }
}

# --- Phase 6: Comment ---
if ($PostComment -and ($script:MergeStatus -match "MERGED" -or $DryRun)) {
    Write-Host "`n### Phase 6: Comment" -ForegroundColor Cyan

    $overrideSection = if ($script:OverrideNotes.Count -gt 0) {
        "`n### Warnings/Overrides`n- " + ($script:OverrideNotes -join "`n- ")
    } else { "" }

    $commentBody = @"
## PR Lifecycle Summary

QA: $script:QaResult
Review: $script:ReviewStatus
Merge: $script:MergeStatus
Post-merge validation: $script:PostMergeValidation
Board movement: $script:BoardMovementStatus
$overrideSection

Notes:
- This PR is integrated into $BaseBranch.
- It is not released to main yet.
- Linked issues should remain 'Pending Release' until the next main release batch.
"@

    if ($DryRun) {
        Write-Host "Dry Run: Would post comment to PR #$PrNumber"
        Write-Host $commentBody
    } else {
        & $gh pr comment $PrNumber --repo $Repo --body $commentBody
        Write-Host "Lifecycle comment posted."
    }
}

# --- Summary Output ---
Write-Host "`n### Final Summary" -ForegroundColor Cyan
Add-Summary "PR Lifecycle Summary"
Add-Summary "--------------------"
Add-Summary "QA: $script:QaResult"
Add-Summary "Review: $script:ReviewStatus"
Add-Summary "Merge: $script:MergeStatus"
Add-Summary "Post-merge validation: $script:PostMergeValidation"
Add-Summary "Board movement: $script:BoardMovementStatus"
if ($script:OverrideNotes.Count -gt 0) {
    Add-Summary "--------------------"
    Add-Summary "Warnings/Overrides:"
    foreach ($note in $script:OverrideNotes) {
        Add-Summary "- $note"
    }
}
Add-Summary "--------------------"
