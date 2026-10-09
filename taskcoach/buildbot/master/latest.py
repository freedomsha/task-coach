#!/usr/bin/python

# 3 lignes de futurize:
# from __future__ import print_function
# from past.builtins import cmp
# from builtins import map
import os
import re
import sys


def findLatest(path, valid):
    rx = re.compile(r"(.*)(\d+\.\d+\.\d+\.\d+)(.*)")

    results = dict()

    for name in os.listdir(path):
        if (
            name.lower().startswith("taskcoach")
            or name.lower().startswith("x-taskcoach")
        ) and valid(name):
            mt = rx.search(name)
            if mt:
                ls = results.get((mt.group(1), mt.group(3)), [])
                ls.append(list(map(int, mt.group(2).split("."))))
                results[(mt.group(1), mt.group(3))] = ls

    packages = []

    # for (part1, part3), versions in results.items():
    for (part1, part3), versions in list(results.items()):
        versions.sort()
        packages.append(
            "%s%s%s" % (part1, ".".join(map(str, versions[-1])), part3)
        )

    packages.sort()

    return packages


def listPath(path):
    def isSource(name):
        if (
            name.endswith(".tar.gz")
            or name.endswith(".src.rpm")
            or name.endswith(".tgz")
        ):
            return True
        if name.endswith(".zip"):
            return not name.endswith("_rev1.zip")
        return False

    # print'<table border="0">'
    print('<table border="0">')

    changelog = os.path.join(path, "changelog_content")
    if os.path.exists(changelog):
        # print '<tr><td colspan="2"><pre>'
        # print file(changelog, 'rb').read()
        # print '</td></tr></pre>'
        # futurize :
        print('<tr><td colspan="2"><pre>')
        # print(file(changelog, 'rb').read())
        # et moi :
        print(open(changelog, "rb").read())
        print("</td></tr></pre>")

    # print'<tr><th colspan="2"><h2>Sources</h2></th></tr>'
    print('<tr><th colspan="2"><h2>Sources</h2></th></tr>')

    for pkgname in findLatest(path, isSource):
        print("<tr>")
        print('<td><img src="source.png" /></td>')
        print("<td>")
        if path == "." or path == "all":
            print(
                '<a href="http://www.fraca7.net/TaskCoach-packages/%s">%s</a>'
                % (pkgname, pkgname)
            )
        else:
            print(
                '<a href="http://www.fraca7.net/TaskCoach-packages/%s/%s">%s</a>'
                % (path, pkgname, pkgname)
            )
        print("</td>")
        print("</tr>")

    print('<tr><th colspan="2"><h2>Binaries</h2></th></tr>')

    for pkgname in findLatest(path, lambda x: not isSource(x)):
        print("<tr>")
        img = "binary.png"
        if pkgname.endswith(".dmg"):
            img = "mac.png"
        elif pkgname.endswith(".exe"):
            img = "windows.png"
        elif pkgname.endswith(".rpm") or pkgname.endswith(".deb"):
            img = "linux.png"
        print('<td><img src="%s" /></td>' % img)
        print("<td>")
        if path == "." or path == "all":
            print(
                '<a href="http://www.fraca7.net/TaskCoach-packages/%s">%s</a>'
                % (pkgname, pkgname)
            )
        else:
            print(
                '<a href="http://www.fraca7.net/TaskCoach-packages/%s/%s">%s</a>'
                % (path, pkgname, pkgname)
            )
        print("</td>")
        print("</tr>")

    print("</table>")
    print("<hr />")


def main(path):
    print("Content-type: text/html")
    print()

    print("<html><head><title>Latest Task Coach builds</title>")
    print(
        '<style type="text/css" media="screen">@import "default.css";</style>'
    )
    print("</head><body><center>")

    if path == "." or path == "all":
        print("<h1>New developments (from trunk)</h1>")
        listPath(".")

    #    if path != '.':
    #        for name in sorted(os.listdir(path), cmp=lambda x, y: cmp(y, x)):  # Feature should come first
    #            if name.startswith('Release') or name.startswith('Feature'):
    #                fname = os.path.join(path, name)
    #                if os.path.isdir(fname):
    #                    if name.startswith('Release'):
    #                        print('<h1>Bug fixes (from %s)</h1>' % name)
    #                    else:
    #                        print('<h1>Experimental features (from %s)</h1>' % name)
    #                    listpath(fname)

    # Dans cet exemple, j'ai remplacé cmp par key pour spécifier la fonction de tri pour sorted,
    # et j'ai utilisé des f-strings pour inclure la variable name dans les chaînes de caractères.
    # Cela rend le code compatible avec Python 3.
    if path != ".":
        for name in sorted(os.listdir(path), key=lambda x: x, reverse=True):  # Feature should come first
            if name.startswith("Release") or name.startswith("Feature"):
                fname = os.path.join(path, name)
                if os.path.isdir(fname):
                    if name.startswith("Release"):
                        print(f"<h1>Bug fixes (from {name})</h1>")
                    else:
                        print(f"<h1>Experimental features (from {name})</h1>")
                    listPath(fname)

    print('<a href="http://www.taskcoach.org/download.html>Back to Task Coach downloads</a>')

    print("</center></body></html>")


if __name__ == "__main__":
    if sys.argv[0].endswith("latest_features.py"):
        main(".")
    elif sys.argv[0].endswith("latest_bugfixes.py"):
        main("branches")
    else:
        main("all")
