# Makefile for cog work.

clean:
	-rm -rf build
	-rm -rf dist
	-rm -f MANIFEST
	-rm -f *.pyc */*.pyc */*/*.pyc */*/*/*.pyc
	-rm -f *.pyo */*.pyo */*/*.pyo */*/*/*.pyo
	-rm -f *$$py.class */*$$py.class */*/*$$py.class */*/*/*$$py.class
	-rm -rf __pycache__ */__pycache__ */*/__pycache__
	-rm -f *.bak */*.bak */*/*.bak */*/*/*.bak
	-rm -f .coverage coverage.xml
	-rm -rf cogapp.egg-info htmlcov

install:
	python setup.py install

test: install
	python scripts/test_cog.py

cover: install
	python scripts/test_cog.py --cover

kit:
	# Needed this on Windows:
	# python setup.py sdist --keep-temp --formats=gztar fixtar --owner=ned --group=cogapp --clean
	python setup.py sdist --formats=gztar

pypi:
	python setup.py register

WEBHOME = c:/ned/web/stellated/pages/code/cog

publish: 
	cp -v *.px $(WEBHOME)
