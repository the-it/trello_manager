clean-pyc :
	echo "######## CLEAN PY CACHE ########"
	find . | grep -E "__pycache__" | xargs rm -rf

update_pip_tool :
	echo "########## UPDATE PIP ##########"
	pip3 install --upgrade pip pip-tools setuptools wheel

pip3 : update_pip_tool
	echo "##### INSTALL REQUIREMENTS #####"
	pip3 install -r requirements.txt

pip3-dev : update_pip_tool
	echo "##### INSTALL REQUIREMENTS #####"
	pip3 install -r requirements.txt -r requirements-dev.txt

update_pip3 : update_pip_tool
	echo "##### UPDATE REQUIREMENTS ######"
	rm requirements.txt requirements-dev.txt || true
	pip-compile --output-file requirements.txt requirements.in
	pip-compile --output-file requirements-dev.txt requirements-dev.in
	pip-sync requirements.txt requirements-dev.txt

unittest :
	echo "########### UNITTEST ###########"
	venv/bin/nose2 -v

safety :
	echo "############ SAFETY ############"
	safety check

flake8 :
	echo "############ FLAKE8 ############"
	flake8

pycodestyle :
	echo "########## PYCODESTYLE #########"
	pycodestyle --show-source --statistics --count src

pylint :
	echo "############ PYLINT ############"
	pylint -j4 --rcfile .pylintrc src

mypy :
	echo "############# MYPY #############"
	mypy src

coverage : clean-coverage
	echo "########### COVERAGE ###########"
	nose2 --with-coverage && \
	coverage xml

clean-coverage :
	echo "######## CLEAN COVERAGE ########"
	rm -rf .coverage coverage.xml .coverage_html || :

coverage-html : coverage
	echo "######### COVERAGE HTML ########"
	coverage html -d .coverage_html
	python -c "import webbrowser, os; webbrowser.open('file://' + os.path.realpath('.coverage_html/index.html'))"

codecov :
	echo "########### CODECOV ############"
	codecov

clean : clean-pyc clean-coverage

quality : safety flake8 pycodestyle pylint mypy

pre-commit : update_pip3 quality unittest

.PHONY : clean, pre-commit quality
