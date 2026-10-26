# deploy.ps1 模板：复制为 deploy.ps1 并填入你自己的服务器信息后使用
# 用途：一键同步本地代码到服务器（tar 打包传输，比逐文件 pscp 快且路径不会错）

param(
    [switch]$Backend,
    [switch]$Frontend,
    [string]$File = ""
)

# ===== 按你的环境修改以下 4 项 =====
$Server = "user@[服务器地址]"          # 例：root@[2400:xxxx] 或 root@1.2.3.4
$RemoteRoot = "/www/wwwroot/你的项目"   # 服务器项目根目录
$Password = "你的SSH密码"
$HostKey = "SHA256:xxxxxxxx"           # 首次 plink 连接时会打印，复制过来即可
# ==================================

$PlinkArgs = "-batch -hostkey `"$HostKey`" -pw $Password $Server"
$PscpArgs = "-batch -hostkey `"$HostKey`" -pw $Password"

function Run($cmd) { plink $PlinkArgs.Split() $cmd }

if ($File -ne "") {
    pscp $PscpArgs $File "$Server`:$RemoteRoot/$($File -replace '\\','/')"
    echo "SINGLE_FILE_SYNCED"
    exit
}

if ($Backend -or (-not $Frontend)) {
    tar -czf "$env:TEMP\backend_sync.tar.gz" app main.py requirements.txt .env.example
    pscp $PscpArgs "$env:TEMP\backend_sync.tar.gz" "$Server`:/tmp/backend_sync.tar.gz"
    Run "cd $RemoteRoot && tar -xzf /tmp/backend_sync.tar.gz && find app -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null; rm -f /tmp/backend_sync.tar.gz && echo BACKEND_SYNCED"
    echo "提示：后端代码需重启 uvicorn / 宝塔 Python 项目才生效"
}

if ($Frontend -or (-not $Backend)) {
    Push-Location frontend
    $env:Path = "$env:LOCALAPPDATA\Programs\nodejs;$env:Path"
    npm run build
    if ($LASTEXITCODE -ne 0) { Pop-Location; echo "BUILD_FAILED"; exit 1 }
    tar -czf "$env:TEMP\dist_sync.tar.gz" -C dist .
    pscp $PscpArgs "$env:TEMP\dist_sync.tar.gz" "$Server`:/tmp/dist_sync.tar.gz"
    Pop-Location
    Run "cd $RemoteRoot/frontend && rm -rf dist_old && mv dist dist_old && mkdir -p dist && tar -xzf /tmp/dist_sync.tar.gz -C dist && rm -f /tmp/dist_sync.tar.gz && rm -rf dist_old && echo FRONTEND_SYNCED"
}
