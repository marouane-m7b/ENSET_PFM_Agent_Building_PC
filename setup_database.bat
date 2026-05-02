@echo off
echo ========================================
echo   PC Builder Agent - Database Setup
echo ========================================
echo.
echo This will create the database and tables
echo Make sure MySQL is running on localhost:3306
echo.
echo Installing dependencies...
uv pip install mysql-connector-python
echo.
echo Initializing database...
uv run python database/init_db.py

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Database 'pc_builder_agent' is ready!
echo You can now run the application.
echo.
pause
