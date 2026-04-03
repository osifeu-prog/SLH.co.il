@echo off
cd /d D:\SLH_PROJECT_V2
chcp 65001 >nul
echo cloudflared is running. log: D:\SLH_PROJECT_V2\logs\tunnel.auto.log
cloudflared tunnel --url http://127.0.0.1:8080 >> "D:\SLH_PROJECT_V2\logs\tunnel.auto.log" 2>&1
