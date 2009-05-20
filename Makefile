# Makefile for cog work.

clean:
	-rm -rf build
	-rm -rf dist
	-rm -f MANIFEST
	-rm -f *.pyc */*.pyc */*/*.pyc */*/*/*.pyc
	-rm -f *.pyo */*.pyo */*/*.pyo */*/*/*.pyo
	-rm -f *$py.class */*$py.class */*/*$py.class */*/*/*$py.class
	-rm -f *.bak */*.bak */*/*.bak */*/*/*.bak
	
install:
	python setup.py install

test: install
	python scripts/test_cog.py

cover: install
	python scripts/test_cog.py --cover

kit:
	python setup.py sdist --formats=gztar,zip

WEBHOME = c:/ned/web/stellated/pages/code/cog

publish: kit
	cp -v dist/*.* $(WEBHOME)
	cp -v *.px $(WEBHOME)
