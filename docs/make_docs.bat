cd "c:\git_hub\samplicity\"
pause

sphinx-apidoc --module-first -f -o docs/source samplicity
sphinx-build -b html docs/source docs/build
pause