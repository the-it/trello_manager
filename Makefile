clean-pyc :
	echo "######## CLEAN PY CACHE ########"
	find . | grep -E "__pycache__" | xargs rm -rf

update_pip_tool :
	echo "########## UPDATE PIP ##########"
	pip3 install --upgrade pip

pip3 : update_pip_tool
	echo "##### INSTALL REQUIREMENTS #####"
	pip3 install -r requirements.txt

update_pip3 : update_pip_tool
	echo "##### UPDATE REQUIREMENTS ######"
	pip3 install pip-tools -U
	rm requirements.txt
	pip-compile --output-file requirements.txt requirements.in
	pip-sync

unittest :
	echo "########### UNITTEST ###########"
	venv/bin/nosetests

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
	venv/bin/nosetests --with-coverage && \
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

pre-commit : pip3 quality unittest

.PHONY : clean, pre-commit quality
