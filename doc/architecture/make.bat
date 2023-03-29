REM Like what you see? Join us!
REM https://www.univention.com/about-us/careers/vacancies/
REM
REM Copyright (C) 2021-2023 Univention GmbH
REM
REM SPDX-License-Identifier: AGPL-3.0-only
REM
REM https://www.univention.com/
REM
REM All rights reserved.
REM
REM The source code of this program is made available under the terms of
REM the GNU Affero General Public License v3.0 only (AGPL-3.0-only) as
REM published by the Free Software Foundation.
REM
REM Binary versions of this program provided by Univention to you as
REM well as other copyrighted, protected or trademarked materials like
REM Logos, graphics, fonts, specific documentations and configurations,
REM cryptographic keys etc. are subject to a license agreement between
REM you and Univention and not subject to the AGPL-3.0-only.
REM
REM In the case you use this program under the terms of the AGPL-3.0-only,
REM the program is provided in the hope that it will be useful, but
REM WITHOUT ANY WARRANTY; without even the implied warranty of
REM MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
REM Affero General Public License for more details.
REM
REM You should have received a copy of the GNU Affero General Public
REM License with the Debian GNU/Linux or Univention distribution in file
REM /usr/share/common-licenses/AGPL-3; if not, see
REM <https://www.gnu.org/licenses/agpl-3.0.txt>.

@ECHO OFF

pushd %~dp0

REM Command file for Sphinx documentation

if "%SPHINXBUILD%" == "" (
	set SPHINXBUILD=sphinx-build
)
set SOURCEDIR=.
set BUILDDIR=_build

if "%1" == "" goto help

%SPHINXBUILD% >NUL 2>NUL
if errorlevel 9009 (
	echo.
	echo.The 'sphinx-build' command was not found. Make sure you have Sphinx
	echo.installed, then set the SPHINXBUILD environment variable to point
	echo.to the full path of the 'sphinx-build' executable. Alternatively you
	echo.may add the Sphinx directory to PATH.
	echo.
	echo.If you don't have Sphinx installed, grab it from
	echo.http://sphinx-doc.org/
	exit /b 1
)

%SPHINXBUILD% -M %1 %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
goto end

:help
%SPHINXBUILD% -M help %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%

:end
popd
