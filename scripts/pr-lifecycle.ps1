[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [int]$PrNumber,

    [string]$Repo = "robertmccarn/echofinder",
    [string]$BaseBranch = "test-main",
    [string]$WorktreeRoot = "Z:\__Swap_Space__",
    [switch]$AutoApprove,
    [switch]$AllowSelfApproval,
    [switch]$AllowManualReviewApprove,
    [switch]$AutoMerge,
    [switch]$ValidateAfterMerge,
    [switch]$MoveBoard,
    [string]$BoardStatus = "Pending Release",
    [string]$ProjectOwner = "robertmccarn",
    [int]$ProjectNumber = 2,
    [switch]$PostComment,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$script:LifecycleSummary = New-Object System.Collections.Generic.List[string]
$script:QaResult = "UNKNOWN"
$script:ReviewStatus = "SKIPPED"
$script:MergeStatus = "SKIPPED"
$script:PostMergeValidation = "SKIPPED"
$script:BoardMovementStatus = "SKIPPED"

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

$git = Resolve-RequiredTool -Name "git"
$gh = Resolve-RequiredTool -Name "gh"
$python = Resolve-RequiredTool -Name "python"

# --- Phase 1: QA ---
Write-Host "### Phase 1: QA" -ForegroundColor Cyan
$reviewScript = Join-Path $PSScriptRoot "review-pr.ps1"
$tempReport = [System.IO.Path]::GetTempFileName()

$reviewArgs = @(
    "-PrNumber", $PrNumber,
    "-Repo", $Repo,
    "-BaseBranch", $BaseBranch,
    "-WorktreeRoot", $WorktreeRoot,
    "-OutputMarkdown", $tempReport
)

try {
    # Run the existing review script
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $reviewScript @reviewArgs
    
    # Capture the recommendation from the end of the report
    $reportContent = Get-Content $tempReport -Raw
    if ($reportContent -match "(APPROVE_READY|NEEDS_MANUAL_REVIEW|REQUEST_CHANGES)\s*$") {
        $script:QaResult = $matches[1]
    }
} finally {
    if (Test-Path $tempReport) { Remove-Item $tempReport }
}

Write-Host "QA Recommendation: $script:QaResult" -ForegroundColor Yellow

# --- Phase 2: Review ---
Write-Host "`n### Phase 2: Review" -ForegroundColor Cyan
$canApprove = ($script:QaResult -eq "APPROVE_READY") -or ($script:QaResult -eq "NEEDS_MANUAL_REVIEW" -and $AllowManualReviewApprove)

if ($AutoApprove) {
    if ($canApprove) {
        $prJson = & $gh pr view $PrNumber --repo $Repo --json author,isDraft,mergeable
        $pr = $prJson | ConvertFrom-Json
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
            $approveResult = & $gh pr review $PrNumber --repo $Repo --approve --body $approveMsg 2>&1
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
$isApproved = ($script:ReviewStatus -in @("APPROVED", "SELF-APPROVED (Validated)", "SKIPPED")) # SKIPPED if already approved

if ($AutoMerge) {
    if ($canApprove -and $isApproved) {
        if ($DryRun) {
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
        $script:MergeStatus = "BLOCKED (Validation/Review criteria not met)"
        Write-Warning "Cannot auto-merge. Review/QA criteria not met."
    }
}

# --- Phase 4: Post-merge Validation ---
if ($script:MergeStatus -eq "MERGED TO $BaseBranch" -and $ValidateAfterMerge) {
    Write-Host "`n### Phase 4: Post-merge Validation" -ForegroundColor Cyan
    if ($DryRun) {
        $script:PostMergeValidation = "PLAN (Dry Run)"
    } else {
        $repoPath = Join-Path $WorktreeRoot "EchoFinder"
        Push-Location $repoPath
        try {
            & $git checkout $BaseBranch
            & $git pull origin $BaseBranch
            & $python -m compileall backend
            
            $pytest = Get-Command pytest -ErrorAction SilentlyContinue
            if ($pytest) { & $pytest }
            
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
if ($MoveBoard -and ($script:MergeStatus -match "MERGED" -or $DryRun)) {
    Write-Host "`n### Phase 5: Board Movement" -ForegroundColor Cyan
    $moveScript = $reviewScript # Reuse logic if possible, or call with flags
    
    $moveArgs = @(
        "-PrNumber", $PrNumber,
        "-Repo", $Repo,
        "-MoveBoard",
        "-BoardStatus", $BoardStatus,
        "-ProjectOwner", $ProjectOwner,
        "-ProjectNumber", $ProjectNumber,
        "-SkipCheckout" # Use current state
    )
    if ($DryRun) { $moveArgs += "-DryRun" }

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $moveScript @moveArgs
    $script:BoardMovementStatus = if ($DryRun) { "PLAN (Dry Run)" } else { $BoardStatus }
}

# --- Phase 6: Comment ---
if ($PostComment -and ($script:MergeStatus -match "MERGED" -or $DryRun)) {
    Write-Host "`n### Phase 6: Comment" -ForegroundColor Cyan
    
    $commentBody = @"
## PR Lifecycle Summary

QA: $script:QaResult
Review: $script:ReviewStatus
Merge: $script:MergeStatus
Post-merge validation: $script:PostMergeValidation
Board movement: $script:BoardMovementStatus

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
Add-Summary "--------------------"
