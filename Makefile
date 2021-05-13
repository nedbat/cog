# Makefile for cog work.

.PHONY: help clean sterile test kit pypi testpypi publish

help:		## Show this help.
	@echo "Available targets:"
	@grep '^[a-zA-Z]' $(MAKEFILE_LIST) | sort | awk -F ':.*?## ' 'NF==2 {printf "  %-26s%s\n", $$1, $$2}'

clean:		## Remove artifacts of test execution, installation, etc.
	-rm -rf build
	-rm -rf dist
	-rm -f MANIFEST
	-rm -f *.pyc */*.pyc */*/*.pyc */*/*/*.pyc
	-rm -f *.pyo */*.pyo */*/*.pyo */*/*/*.pyo
	-rm -f *$$py.class */*$$py.class */*/*$$py.class */*/*/*$$py.class
	-rm -rf __pycache__ */__pycache__ */*/__pycache__
	-rm -f *.bak */*.bak */*/*.bak */*/*/*.bak
	-rm -f .coverage .coverage.* coverage.xml
	-rm -rf cogapp.egg-info htmlcov

sterile: clean		## Remove all non-controlled content.
	-rm -rf .tox*
	-rm -rf .pytest_cache .mutmut-cache

test:			## Run the test suite.
	tox

kit:			## Build distribution kits.
	python setup.py sdist bdist_wheel
	twine check dist/*

pypi:			## Upload kits to PyPI.
	twine upload dist/*

testpypi:		## Upload kits to test PyPI
	twine upload --repository testpypi dist/*

WEBHOME = ~/web/stellated/pages/code/cog

publish:		## Move doc page to nedbat.com home.
	cp -v *.px $(WEBHOME)
