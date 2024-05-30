from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()
from builtins import *
from fabric.api import local


def clean():
	"Remove all generated files"
	local("rm -rf build dist")
	local("find . -name *.pyc -delete")


def test():
	"Run unittests"
	local('nosetests -v --with-coverage')
	local('coverage html')


def html():
	"Generate Sphinx documentation"
	local("sphinx-build -b html -d build/doctrees docs build/html")


def build():
	local("python setup.py build")


def install():
	local("python setup.py install")


def upload_docs():
	local("python setup.py upload_docs --upload-dir build/html")
