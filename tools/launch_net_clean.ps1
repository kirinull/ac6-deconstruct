# launch_net_clean.ps1 -- launch a .NET Framework program from a DSH bash session
#
# WHY THIS EXISTS
# ---------------
# The DSH host loads @deepseek-ai/dsh-http-proxy, which publishes proxy settings
# under BOTH casings on purpose (undici reads the lowercase name first):
#
#     lib/index.js:  POLICY_ENV_NAMES = {
#                      httpProxy:  ["http_proxy",  "HTTP_PROXY"],
#                      httpsProxy: ["https_proxy", "HTTPS_PROXY"],
#                      noProxy:    ["no_proxy",    "NO_PROXY"]
#                    }
#     lib/index.js:  process.env[name] = value;      // both casings written
#
# That env block is inherited by every child process. .NET Framework builds its
# environment dictionary with a case-INSENSITIVE comparer, so the duplicate keys
# throw:
#
#     System.ArgumentException: An item with the same key has already been added.
#     Dictionary key: "no_proxy"  Key being added: "NO_PROXY"
#
# Visual Studio (devenv.exe) reads that dictionary during startup and dies with
# "由于出现错误，无法启动 Visual Studio。" -- reproducible only when launched from
# a DSH-spawned shell. Launching from Explorer/Start Menu inherits a clean block
# and works fine, because Explorer never saw those variables.
#
# This wrapper drops ONLY the lowercase duplicates, keeps the uppercase ones, and
# then starts the target. Proxy behaviour is preserved (HTTP_PROXY/HTTPS_PROXY/
# NO_PROXY remain set); only the ambiguous lowercase aliases go away, and only
# inside this wrapper's own process tree -- the DSH host itself is untouched.
#
# USAGE
# -----
#   powershell -NoProfile -File launch_net_clean.ps1 -Exe <path> [-ExeArgs a,b] [-Wait] [-DryRun]
#
# EXAMPLES
#   # open the UE5 solution in VS2022
#   powershell -NoProfile -File launch_net_clean.ps1 `
#     -Exe '<VS2022>\Common7\IDE\devenv.exe' `
#     -ExeArgs '<UE_PROJECTS>\AC6Proto\AC6Proto.sln'
#
#   # generate VS project files for a .uproject (also .NET Framework)
#   powershell -NoProfile -File launch_net_clean.ps1 `
#     -Exe '<UE_ENGINE>\Engine\Binaries\Win64\UnrealVersionSelector.exe' `
#     -ExeArgs '/projectfiles','<UE_PROJECTS>\AC6Proto\AC6Proto.uproject'

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]   $Exe,
    [string[]]                               $ExeArgs = @(),
    [switch]                                 $Wait,
    [switch]                                 $DryRun
)

$ErrorActionPreference = 'Stop'

# Lowercase names that duplicate an uppercase counterpart. all_proxy included
# because a proxy manager may add it even though dsh-http-proxy never writes it.
$duplicates = @('http_proxy', 'https_proxy', 'no_proxy', 'all_proxy', 'ws_proxy', 'wss_proxy')

# --- 1. self-check BEFORE cleanup: show the failure we are here to avoid ------
$before = $null
try {
    $before = (Get-ChildItem Env: -ErrorAction Stop).Count
    Write-Host "[self-check] Env: enumerates cleanly ($before vars) - cleanup may be unnecessary"
} catch {
    Write-Host "[self-check] Env: enumeration FAILS: $($_.Exception.Message)"
    Write-Host "[self-check] this is the duplicate-casing conflict; cleaning up"
}

# --- 2. drop lowercase duplicates, keep uppercase -----------------------------
$removed = @()
foreach ($n in $duplicates) {
    if ($null -ne [Environment]::GetEnvironmentVariable($n)) {
        $removed += $n
        [Environment]::SetEnvironmentVariable($n, $null)
    }
}
if ($removed.Count -gt 0) {
    Write-Host "[cleanup] removed lowercase duplicates: $($removed -join ', ')"
} else {
    Write-Host "[cleanup] nothing to remove"
}

# --- 3. verify the fix actually took ------------------------------------------
try {
    $after = (Get-ChildItem Env: -ErrorAction Stop).Count
    Write-Host "[verify] Env: enumerates cleanly now ($after vars)"
} catch {
    Write-Host "[verify] STILL BROKEN: $($_.Exception.Message)"
    exit 2
}

# Report EXACTLY which proxy variables survived, with their real casing.
#
# WARNING -- do not "verify" this with [Environment]::GetEnvironmentVariable(name):
# on Windows that lookup is case-INSENSITIVE, so asking for 'HTTP_PROXY' returns a
# value even when only the lowercase 'http_proxy' exists. It cannot distinguish the
# two, and it will happily report a fix that did not happen. Only a case-preserving
# enumeration shows the truth.
$surviving = @()
foreach ($entry in (Get-ChildItem Env:)) {
    if ($entry.Name -match 'proxy') { $surviving += ("{0} = {1}" -f $entry.Name, $entry.Value) }
}
Write-Host "[verify] proxy vars now present (real casing):"
if ($surviving.Count -eq 0) {
    Write-Host "           (none - traffic will go direct)"
} else {
    foreach ($s in ($surviving | Sort-Object)) { Write-Host "           $s" }
}

# --- 4. launch ----------------------------------------------------------------
$resolved = $Exe
if (-not (Test-Path -LiteralPath $Exe)) {
    # A bare command name (e.g. powershell.exe) is not resolvable by Test-Path;
    # fall back to a PATH lookup before giving up.
    $cmd = Get-Command $Exe -ErrorAction SilentlyContinue
    if ($cmd) {
        $resolved = $cmd.Source
        Write-Host "[launch] resolved '$Exe' -> $resolved"
    } else {
        Write-Host "[launch] FAIL - executable not found: $Exe"
        exit 3
    }
}

Write-Host "[launch] $resolved $($ExeArgs -join ' ')"
if ($DryRun) {
    Write-Host "[launch] -DryRun set; not starting anything"
    exit 0
}

if ($Wait) {
    & $resolved @ExeArgs
    exit $LASTEXITCODE
} else {
    # Start-Process rejects an empty -ArgumentList, so only pass it when non-empty.
    if ($ExeArgs.Count -gt 0) {
        Start-Process -FilePath $resolved -ArgumentList $ExeArgs | Out-Null
    } else {
        Start-Process -FilePath $resolved | Out-Null
    }
    Write-Host "[launch] started (detached)"
    exit 0
}
