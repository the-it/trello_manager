clean-pyc :
	echo "######## CLEAN PY CACHE ########"
	find . | grep -E "__pycache__" | xargs rm -rf

pip3 :
	echo "##### INSTALL REQUIREMENTS #####"
	pip3 install -r requirements.txt

unittest :
	echo "########### UNITTEST ###########"
	venv/bin/nosetests

coverage : clean-coverage
	echo "########### COVERAGE ###########"
	export PYWIKIBOT2_NO_USER_CONFIG=1 && \
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

codacy :
	echo "############ CODACY ############"
	python-codacy-coverage -r coverage.xml

clean : clean-pyc clean-coverage

pre-commit : unittest

.PHONY : clean, pre-commit
