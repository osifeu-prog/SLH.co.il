# -*- coding: utf-8 -*-
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from datetime import datetime

app = FastAPI(title="SLH Airdrop API")

# ??????
TON_WALLET = os.getenv("TON_WALLET", "UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp")

@app.get("/")
async def root():
    return {"message": "SLH Airdrop API", "status": "active", "version": "3.0.0"}

@app.get("/health")
async def health_check():
    return JSONResponse({
        "status": "healthy",
        "service": "SLH Airdrop API",
        "timestamp": datetime.now().isoformat(),
        "version": "3.0.0",
        "components": {
            "api": "running",
            "bot": "separate_service",
            "database": "json_files"
        }
    })

@app.get("/api/stats")
async def get_stats():
    """????? ?????????"""
    return JSONResponse({
        "status": "success",
        "stats": {
            "total_users": 38,
            "verified_users": 22,
            "total_transactions": 22,
            "confirmed_transactions": 22,
            "pending_transactions": 0,
            "available_slots": 978,
            "total_ton": 976.8,
            "updated_at": datetime.now().isoformat()
        }
    })

@app.get("/admin/dashboard")
async def admin_dashboard(admin_key: str = None):
    """???? ????? ?????"""
    if admin_key != "airdrop_admin_2026":
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    html_content = f"""
<!DOCTYPE html>
<html dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SLH Airdrop - Executive Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: rgba(255, 255, 255, 0.95); padding: 30px; border-radius: 20px; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }}
        .header h1 {{ color: #2c3e50; font-size: 2.5rem; margin: 0; }}
        .header p {{ color: #666; margin: 10px 0 0 0; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 25px; margin-bottom: 30px; }}
        .stat-card {{ background: rgba(255, 255, 255, 0.95); padding: 25px; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.08); transition: transform 0.3s; }}
        .stat-card:hover {{ transform: translateY(-5px); }}
        .stat-card h3 {{ margin-top: 0; color: #2c3e50; }}
        .stat-number {{ font-size: 3rem; font-weight: 800; margin: 10px 0; }}
        .stat-label {{ color: #666; }}
        .dashboard {{ background: rgba(255, 255, 255, 0.95); padding: 30px; border-radius: 20px; }}
        .services {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 30px; }}
        .service-card {{ background: white; padding: 20px; border-radius: 10px; border-left: 5px solid #3498db; }}
        .status-online {{ color: #27ae60; font-weight: bold; }}
        .status-offline {{ color: #e74c3c; font-weight: bold; }}
        .wallet-box {{ background: #e8f4fd; padding: 15px; border-radius: 10px; font-family: monospace; word-break: break-all; margin: 20px 0; }}
        .links a {{ display: inline-block; background: #3498db; color: white; padding: 10px 20px; margin: 10px; border-radius: 5px; text-decoration: none; }}
        .links a:hover {{ background: #2980b9; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>?? SLH Airdrop - Executive Dashboard</h1>
            <p>????? ????? ????? ?????? ??????? | ?????: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card" style="border-left: 5px solid #3498db;">
                <h3>?? ??????? ??????</h3>
                <div class="stat-number">38</div>
                <div class="stat-label">???? 1,000 ???</div>
            </div>
            <div class="stat-card" style="border-left: 5px solid #27ae60;">
                <h3>?? ?????? ???????</h3>
                <div class="stat-number">22</div>
                <div class="stat-label">44.4 TON ?? ???</div>
            </div>
            <div class="stat-card" style="border-left: 5px solid #f39c12;">
                <h3>?? TON ?????</h3>
                <div class="stat-number">976.8</div>
                <div class="stat-label">???? 44,400 ???</div>
            </div>
            <div class="stat-card" style="border-left: 5px solid #9b59b6;">
                <h3>?? ?????? ??????</h3>
                <div class="stat-number">978</div>
                <div class="stat-label">??????? ?????</div>
            </div>
        </div>
        
        <div class="dashboard">
            <h2>?? ???? TON ????? ???????</h2>
            <div class="wallet-box">{TON_WALLET}</div>
            <p><small>??????? ????? 44.4 TON ?????? ??</small></p>
            
            <h2>? ????? ???????</h2>
            <div class="services">
                <div class="service-card">
                    <h3>?? ??? ?????</h3>
                    <p class="status-online">?? ???? ?????</p>
                    <p>@SLH_AIR_bot</p>
                    <p>????? ????? ???????? ????????</p>
                </div>
                <div class="service-card">
                    <h3>?? API ?????</h3>
                    <p class="status-online">?? ???? ?????</p>
                    <p>????: 8000</p>
                    <p>???? ????? ??????</p>
                </div>
                <div class="service-card">
                    <h3>?? ????? ??????</h3>
                    <p class="status-online">?? JSON Files</p>
                    <p>????? ??????</p>
                    <p>????? ???????</p>
                </div>
            </div>
            
            <h2>?? ??????? ??????</h2>
            <div class="links">
                <a href="/health" target="_blank">? ????? ????? API</a>
                <a href="/api/stats" target="_blank">?? ?????????? API</a>
                <a href="https://t.me/SLH_AIR_bot" target="_blank">?? ??? ??? ?????</a>
                <a href="https://railway.app/project/airdrop" target="_blank">? Railway Dashboard</a>
            </div>
            
            <h2>?? ??????? ??????</h2>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px;">
                <p>? <strong>??? 1:</strong> ??? ????? ????? - <span style="color: green;">?????</span></p>
                <p>? <strong>??? 2:</strong> ????? ????? ???????? - <span style="color: green;">?????</span></p>
                <p>?? <strong>??? 3:</strong> ????? ???? ?????? - <span style="color: orange;">??????</span></p>
                <p>? <strong>??? 4:</strong> ????????? TON Blockchain - <span style="color: blue;">??????</span></p>
                <p>? <strong>??? 5:</strong> ???? ????? ????? - <span style="color: blue;">??????</span></p>
            </div>
            
            <div style="margin-top: 30px; padding: 20px; background: #2c3e50; color: white; border-radius: 10px;">
                <h3 style="margin-top: 0;">?? ????? ????? ??????</h3>
                <p>?????? ?????:</p>
                <ul>
                    <li>?? ??? ????? ??????? ???</li>
                    <li>?? ????? ??????? ???????</li>
                    <li>?? ??? ??????? ??????</li>
                    <li>?? ????? Scalable ?-Railway</li>
                    <li>?? ????? ????? ?????? ??????</li>
                </ul>
            </div>
        </div>
        
        <div style="text-align: center; color: white; margin-top: 40px; padding: 20px;">
            <p>ן¿½ 2026 SLH Airdrop System | ???? ?? ??? Osif Ungar | ?????: @Osif83</p>
            <p>????: 3.0.0 | ??? ?????: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
    
    return HTMLResponse(content=html_content)

# ??? ?? ?-API
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"?? Starting API Server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)



