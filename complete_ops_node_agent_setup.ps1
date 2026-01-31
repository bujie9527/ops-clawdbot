# 在网络可用时运行此脚本，完成 ops-node-agent 独立仓库与 submodule 转换
# 前置：已在 GitHub 创建空仓库 https://github.com/bujie9527/ops-node-agent

$ErrorActionPreference = "Stop"

Write-Host "=== 1. 推送 ops-node-agent 到 GitHub ===" -ForegroundColor Cyan
$tmp = "d:\AI_Hub_ops_node_agent_temp"
if (Test-Path $tmp) {
    Set-Location $tmp
    git push -u origin main
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Push failed. Check network and GitHub access." -ForegroundColor Red
        exit 1
    }
    Set-Location d:\AI_Hub
    Remove-Item $tmp -Recurse -Force
    Write-Host "Push OK, temp dir removed." -ForegroundColor Green
} else {
    Write-Host "Temp dir not found. Run initial setup first." -ForegroundColor Yellow
}

Write-Host "`n=== 2. 将 ops-node-agent 转为 submodule ===" -ForegroundColor Cyan
Set-Location d:\AI_Hub

git rm -r --cached ops-node-agent 2>$null
Remove-Item -Path "ops-node-agent" -Recurse -Force -ErrorAction SilentlyContinue
git submodule add https://github.com/bujie9527/ops-node-agent.git ops-node-agent
git add .gitmodules ops-node-agent
git commit -m "refactor: ops-node-agent as submodule"
git push

Write-Host "`n=== Done ===" -ForegroundColor Green
