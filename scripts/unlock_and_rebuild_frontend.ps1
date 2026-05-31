# Attempt to stop processes that may hold the file
Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process -Name code -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Remove read-only attribute if set
attrib -R "D:\Rag Chatter\frontend\node_modules\@next\swc-win32-x64-msvc\next-swc.win32-x64-msvc.node" 2>$null

# Take ownership and grant full control
takeown /F "D:\Rag Chatter\frontend\node_modules\@next\swc-win32-x64-msvc\next-swc.win32-x64-msvc.node"
icacls "D:\Rag Chatter\frontend\node_modules\@next\swc-win32-x64-msvc\next-swc.win32-x64-msvc.node" /grant "$Env:USERNAME:F" /C

Remove-Item -LiteralPath 'D:\Rag Chatter\frontend\node_modules' -Recurse -Force -ErrorAction SilentlyContinue
Set-Location -LiteralPath 'D:\Rag Chatter\frontend'
npm ci --prefer-offline --no-audit --no-fund
npm run build
