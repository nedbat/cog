# Makefile for cog work.

# A command to get the current version from cogapp.py
VERSION := $$(python -c "import cogapp.cogapp; print(cogapp.cogapp.__version__)")

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

.PHONY: cogdoc lintdoc dochtml

# Normally I'd put this in a comment in index.px, but the
# quoting/escaping would be impossible.
COGARGS = -cP --markers='{{{cog }}} {{{end}}}' docs/running.rst

cogdoc:			## Run cog to keep the docs correct.
	python -m cogapp -r $(COGARGS)

lintdoc:		## Check that the docs are up-to-date.
	@python -m cogapp --check --diff $(COGARGS); \
	if [ $$? -ne 0 ]; then \
		echo 'Docs need to be updated: `make cogdoc`'; \
		exit 1; \
	fi

dochtml:		## Build local docs.
	$(MAKE) -C docs html

# Release

.PHONY: dist pypi testpypi tag release check_release _check_credentials _check_manifest _check_tree _check_version

dist:			## Build distribution artifacts.
	python -m build
	twine check dist/*

pypi:			## Upload distributions to PyPI.
	twine upload --verbose dist/*

testpypi:		## Upload distributions to test PyPI
	twine upload --verbose --repository testpypi --password $$TWINE_TEST_PASSWORD dist/*

tag:			## Make a git tag with the version number
	git tag -s -m "Version $(VERSION)" v$(VERSION)
	git push --all

release: _check_credentials clean check_release dist pypi tag ## Do all the steps for a release
	@echo "Release $(VERSION) complete!"

check_release: _check_manifest _check_tree _check_version ## Check that we are ready for a release
	@echo "Release checks passed"

_check_credentials:
	@if [[ -z "$$TWINE_PASSWORD" ]]; then \
		echo 'Missing TWINE_PASSWORD'; \
		exit 1; \
	fi

_check_manifest:
	python -m check_manifest

_check_tree:
	@if [[ -n $$(git status --porcelain) ]]; then \
		echo 'There are modified files! Did you forget to check them in?'; \
		exit 1; \
	fi

_check_version:
	@if git tag | grep -q -w v$(VERSION); then \
		echo 'A git tag for this version exists! Did you forget to bump the version?'; \
		exit 1; \
	fi
