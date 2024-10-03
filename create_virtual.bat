@echo off

rem Get the current date in the format YYYYMMDD
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set "datetime=%%I"
set "datestamp=%datetime:~0,4%%datetime:~4,2%%datetime:~6,2%"

rem Set the directory for virtual environments including the current date
set "venv_dir=C:\venv\samplicity"

echo;
echo ####################
echo;
echo Welcome to Samplicity
echo;
echo ####################
echo;

rem Check if the virtual environment folder exists
if exist "%venv_dir%" (
    rem If it exists, remove it
    echo Removing existing virtual environment...
    rmdir /s /q "%venv_dir%"
)

rem Create the directory for the virtual environment

echo Creating directory for the Samplicity virtual environment...
mkdir "%venv_dir%"

rem Try creating a new virtual environment using `py -m` and fallback to `python -m` if it fails
echo Creating new Samplicity virtual environment...
py -m venv "%venv_dir%"
if %errorlevel% neq 0 (
    echo Creating new Samplicity virtual environment using python -m venv...
    python -m venv "%venv_dir%"
)

rem Activate the virtual environment
echo Activating virtual Samplicity environment...
call "%venv_dir%\Scripts\activate"

rem Updating pip
echo Updating PIP for Samplicity virtual environment...
pip install --upgrade pip

rem Try installing packages without proxy first, if it fails then set proxy and try again
rem We don't have to worry about a requirements file, the Samplicity package should install
rem all of the required packages.
echo Installing the Samplicity package...
pip install git+https://bitbucket.org/omi-it/samplicity.git
if %errorlevel% neq 0 (
    echo Installing packages with proxy...
    set https_proxy=http://10.1.0.1:70
    pip install git+https://bitbucket.org/omi-it/samplicity.git
)

echo All done.
pause
