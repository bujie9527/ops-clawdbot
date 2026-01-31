# 完整 API 测试流程（需在 cloud_console 目录下运行，且服务已启动）
# .\test_api.ps1

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

$base = "http://127.0.0.1:8000"
$h = @{
    "Authorization" = "Bearer changeme_node_token_project_a"
    "Content-Type"  = "application/json"
}

Write-Host "=== 1. 注册节点 ===" -ForegroundColor Cyan
$r = Invoke-RestMethod -Uri "$base/api/nodes/register" -Method POST -Headers $h -Body (Get-Content test_register.json -Raw)
Write-Host ($r | ConvertTo-Json)

Write-Host "`n=== 2. 创建任务 ===" -ForegroundColor Cyan
$r = Invoke-RestMethod -Uri "$base/api/tasks/create" -Method POST -Headers $h -Body (Get-Content test_create_task.json -Raw)
Write-Host ($r | ConvertTo-Json)
$taskId = $r.task_id

Write-Host "`n=== 3. 拉取任务 ===" -ForegroundColor Cyan
$r = Invoke-RestMethod -Uri "$base/api/nodes/node-1/tasks?state=CREATED" -Method GET -Headers $h
Write-Host ($r | ConvertTo-Json -Depth 5)

Write-Host "`n=== 4. 回传任务结果 (task_id=$taskId) ===" -ForegroundColor Cyan
$body = (Get-Content test_report.json -Raw)
$r = Invoke-RestMethod -Uri "$base/api/tasks/$taskId/report" -Method POST -Headers $h -Body $body
Write-Host ($r | ConvertTo-Json)

Write-Host "`n=== 测试完成 ===" -ForegroundColor Green
