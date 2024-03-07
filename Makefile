# Makefile for cog work.

.PHONY: help clean sterile test

help:			## Show this help.
	@echo "Available targets:"
	@grep '^[a-zA-Z]' $(MAKEFILE_LIST) | sort | awk -F ':.*?## ' 'NF==2 {printf "  %-26s%s\n", $$1, $$2}'

clean:			## Remove artifacts of test execution, installation, etc.
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
	-rm -rf docs/_build

sterile: clean		## Remove all non-controlled content.
	-rm -rf .tox*
	-rm -rf .*_cache

test:			## Run the test suite.
	tox -q

# Docs

.PHONY: cogdoc dochtml

cogdoc:			## Run cog to keep the docs correct.
	# Normally I'd put this in a comment in index.px, but the
	# quoting/escaping would be impossible.
	python -m cogapp -crP --markers='{{{cog }}} {{{end}}}' docs/running.rst

dochtml:		## Build local docs.
	$(MAKE) -C docs html

# Release

.PHONY: dist pypi testpypi check_release

dist:			## Build distribution artifacts.
	python -m build
	twine check dist/*

pypi:			## Upload distributions to PyPI.
	twine upload --verbose dist/*

testpypi:		## Upload distributions to test PyPI
	twine upload --verbose --repository testpypi --password $$TWINE_TEST_PASSWORD dist/*

check_release: _check_manifest ## Check that we are ready for a release
	@echo "Release checks passed"

_check_manifest:
	python -m check_manifest
