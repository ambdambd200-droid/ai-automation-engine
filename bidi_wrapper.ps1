<#
.SYNOPSIS
    Wraps any command with the Arabic RTL terminal rendering fix.

.DESCRIPTION
    Runs a command through bidi_terminal.py so that Arabic text is properly
    right-aligned and word-reversed for terminals without bidi support.

    NEVER mutates the original text — only changes visual rendering.

.PARAMETER Command
    The command to run (e.g., "python hunt.py --gather")

.PARAMETER Raw
    If set, runs the command directly without the RTL fix (passthrough).

.EXAMPLE
    .\bidi_wrapper.ps1 "python hunt.py --gather"
    # Runs hunt.py with Arabic RTL fix applied to all output

.EXAMPLE
    .\bidi_wrapper.ps1 "python daily.py" -Raw
    # Runs daily.py without any RTL fix (passthrough)

.EXAMPLE
    .\bidi_wrapper.ps1 "codebuff"
    # Runs codebuff CLI with Arabic RTL fix

.NOTES
    For interactive CLIs, uses --exec mode. For non-interactive, uses pipe.
    Only fixes stdout. Interactive TUI apps may not work perfectly.
#>
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Command,

    [switch]$Raw
)

$Python = "C:\Users\A\AppData\Local\Programs\Python\Python312\python.exe"
$Script = Join-Path $PSScriptRoot "bidi_terminal.py"

if (-not (Test-Path $Script)) {
    Write-Error "bidi_terminal.py not found at: $Script"
    exit 1
}

if ($Raw) {
    # Passthrough mode — run the command directly
    Invoke-Expression $Command
    exit $LASTEXITCODE
}

# Wrap the command through the bidi filter
Write-Host "[bidi_wrapper] Running with Arabic RTL fix: $Command" -ForegroundColor DarkGray
Write-Host "[bidi_wrapper] Pass -Raw to disable." -ForegroundColor DarkGray

# Use --exec mode: run the command and fix its output
& $Python $Script --exec $Command
