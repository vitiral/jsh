check: fix test
	# SHIP IT!

ship: check
	rm -rf pycheck/ dist/
	virtualenv --python=python3 pycheck
	pycheck/bin/pip install .
	py3/bin/python setup.py sdist
	# run: py3/bin/twine upload dist/*


init:
	# python2
	virtualenv --python=python2 py2
	py2/bin/pip install pytest
	# python3
	virtualenv --python=python3 py3
	py3/bin/pip install pytest yapf pylint twine

fix:
	py3/bin/yapf --in-place -r jshlib.py bin/jsh tests

lint:
	py3/bin/pylint jshlib.py bin/jsh

test2:
	# Testing python2
	PYTHONHASHSEED=42 py2/bin/py.test -vvv

test3:
	# Testing python3
	py3/bin/py.test -vvv

test: test3 test2

clean:
	rm -rf py2 py3 dist anchor_txt.egg-info
