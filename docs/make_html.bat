cd "c:\git_hub\samplicity\"
pause

rem sphinx-apidoc --module-first -f -o docs/source samplicity/prem_res.py samplicity/reinsurance
sphinx-build -a -b html docs/source docs/build
pause