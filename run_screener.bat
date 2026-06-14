@echo off
cd /d "%~dp0"
echo.
echo Options Call Screener - starting on port 8503
echo.
echo On THIS PC:     http://localhost:8503
echo On your PHONE:  http://YOUR-PC-IP:8503  (same WiFi; find IP: ipconfig)
echo Away from home: use Tailscale (see PHONE_ACCESS.md) or keep PC on + VPN
echo.
echo Leave this window open while using the screener.
echo.
streamlit run options_call_screener/app.py
pause
