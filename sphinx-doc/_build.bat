@ECHO OFF

if "%SPHINXBUILD%" == "" (
	set SPHINXAPIDOC=sphinx-apidoc
)
"%SPHINXAPIDOC%" -f -H smartbus -o ./ ../src

make html
