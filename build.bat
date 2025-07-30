@echo off
echo Building HealthCare.exe...
"C:\Users\akash\AppData\Roaming\Python\Python313\Scripts\pyinstaller.exe" --onefile --console ^
--add-data "D:\HealthDocter\sound\Ak.mp3;sound" ^
--add-data "C:\Users\akash\AppData\Roaming\Python\Python313\site-packages\plyer\platforms;plyer\platforms" ^
D:\HealthDocter\HealthCare.py

echo Build complete! Check the dist\ folder.
pause
