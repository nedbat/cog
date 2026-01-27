# Makefile for cog work.

.DEFAULT_GOAL := help

### Development

.PHONY: venv install test

venv: .venv		#- Create a development virtualenv.
.venv:
	uv venv --python=3.10 --prompt=cog

install: venv		#- Install the development tools.
	uv pip sync dev-requirements.txt

test:			#- Run the test suite.
	tox -q

# Limit to packages that were released more than 10 days ago.
# https://blog.yossarian.net/2025/11/21/We-should-all-be-using-dependency-cooldowns
upgrade: export UV_CUSTOM_COMPILE_COMMAND=make upgrade
upgrade: export UV_EXCLUDE_NEWER=P10D
upgrade: venv		#- Upgrade development tool pins.
	uv pip compile -q --universal --upgrade -o dev-requirements.txt dev-requirements.in

### Docs

.PHONY: cogdoc lintdoc dochtml

# Normally I'd put this in a comment in index.px, but the
# quoting/escaping would be impossible.
COGARGS = -cP --markers='{{{cog }}} {{{end}}}' docs/running.rst

cogdoc:			#- Run cog to keep the docs correct.
	python -m cogapp -r $(COGARGS)

lintdoc:		#- Check that the docs are up-to-date.
	@python -m cogapp --check --check-fail-msg='Docs need to be updated: `make cogdoc`' --diff $(COGARGS)

dochtml:		#- Build local docs.
	$(MAKE) -C docs html

### Release

.PHONY: check_release release dist pypi testpypi tag

# A command to get the current version from cogapp.py
VERSION := $$(python -c "import cogapp.cogapp; print(cogapp.cogapp.__version__)")

check_release: clean dist _check_manifest _check_tree _check_version #- Check that we are ready for a release.
	@echo "Release checks passed"

release: _check_credentials clean check_release dist pypi tag #- Do all the steps for a release.
	@echo "Release $(VERSION) complete!"

dist:			#- Build distribution artifacts (part of release).
	python -m build
	twine check dist/*

pypi:			#- Upload distributions to PyPI (part of release).
	twine upload --verbose dist/*

tag:			#- Make a git tag with the version number (part of release).
	git tag -s -m "Version $(VERSION)" v$(VERSION)
	git push --all

testpypi:		#- Upload distributions to test PyPI.
	twine upload --verbose --repository testpypi --password $$TWINE_TEST_PASSWORD dist/*

.PHONY: _check_credentials _check_manifest _check_tree _check_version

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

### Utilities

.PHONY: help clean sterile

help:			#- Show this help.
	@# Adapted from https://www.thapaliya.com/en/writings/well-documented-makefiles/
	@# Markdown-inspired syntax is used in comments to print help.
	@# Lines starting with '###' are section headers.
	@# Targets with bullet-like '#- ' comments are shown.
	@echo Available targets:
	@awk -F ':.*#-' '/^[^: ]+:.*#-/{printf "  \033[1m%-20s\033[m %s\n",$$1,$$2} /^###/{printf "\n%s\n",substr($$0,5)}' $(MAKEFILE_LIST)

clean:			#- Remove artifacts of test execution, installation, etc.
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

sterile: clean		#- Remove all non-controlled content.
	-rm -rf .tox*
	-rm -rf .*_cache
