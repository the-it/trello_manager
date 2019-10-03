clean-pyc :
	echo "######## CLEAN PY CACHE ########"
	find . | grep -E "__pycache__" | xargs rm -rf

pip3 :
	echo "##### INSTALL REQUIREMENTS #####"
	pip3 install -r requirements.txt

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

pre-commit : quality unittest

.PHONY : clean, pre-commit quality
