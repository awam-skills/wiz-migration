@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title 批量复制 _Attachments 目录

:: ====================== 请修改这里的路径 ======================
:: 源目录：为知笔记数据目录（自动生成时会替换）
set "SOURCE_DIR=SOURCE_DIR_PLACEHOLDER"
:: 目标目录：导出笔记的存放位置（自动生成时会替换）
set "TARGET_DIR=TARGET_DIR_PLACEHOLDER"
:: ==============================================================

echo ==============================================
echo 批量复制 _Attachments 目录
echo 功能：已存在自动跳过，可重复执行，不覆盖
echo ==============================================
echo 源目录：%SOURCE_DIR%
echo 目标目录：%TARGET_DIR%
echo.

:: 检查源目录是否存在
if not exist "%SOURCE_DIR%" (
    echo ❌ 源目录不存在！
    echo 请确认路径是否正确：
    echo   %SOURCE_DIR%
    pause
    exit /b 1
)

set COUNT=0
set SKIP=0
set FAIL=0

for /d /r "%SOURCE_DIR%" %%d in (*_Attachments) do (
 set "FULL_PATH=%%d"
 set "REL_PATH=!FULL_PATH:%SOURCE_DIR%=!"
 set "DEST_PATH=%TARGET_DIR%!REL_PATH!"

 echo 源目录：!FULL_PATH!
 echo 目标路径：!DEST_PATH!

 if exist "!DEST_PATH!" (
 echo ⏭️ 已存在，跳过：!REL_PATH!
 set /a SKIP+=1
 ) else (
 mkdir "!DEST_PATH!" 2>nul
 if exist "!DEST_PATH!" (
   xcopy "!FULL_PATH!\*" "!DEST_PATH!\" /E /H /C /R /Q >nul
   if errorlevel 1 (
     echo ❌ 复制失败：!REL_PATH!
     set /a FAIL+=1
   ) else (
     echo ✅ 复制成功：!REL_PATH!
     set /a COUNT+=1
   )
 ) else (
   echo ❌ 无法创建目录：!DEST_PATH!
   set /a FAIL+=1
 )
 )
 echo.
)

echo ==============================================
echo 任务完成
echo 本次新增复制：!COUNT! 个
echo 已存在跳过：!SKIP! 个
echo 失败目录：!FAIL! 个
echo ==============================================

if !FAIL! gtr 0 (
    echo.
    echo ⚠️  有 !FAIL! 个目录复制失败，请检查权限或磁盘空间
)

pause
exit /b 0
