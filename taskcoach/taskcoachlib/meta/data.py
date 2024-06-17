# -*- coding: utf-8 -*-

"""
Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>

Task Coach is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Task Coach is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# pylint: disable=C0103

# Edit these for every release:

version = "1.5.0"  # Current version number of the application
tskversion = 37  # Current version number of the task file format, changed to 37 for release 1.3.23.
release_day = "5"  # Day number of the release, 1-31, as string
release_month = "September"  # Month of the release in plain English
release_year = "2020"  # Year of the release as string
release_status = "stable"  # One of 'alpha', 'beta', 'stable'

# No editing needed below this line for doing a release.

import datetime
import re

try:
    from taskcoachlib.meta.revision import (
        revision,
    )  # pylint: disable=F0401,W0611
except ImportError:
    revision = None

months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

if revision:  # Buildbot sets revision
    # Decrement version because this version isn't released yet. This
    # assumes that version components are < 100; 99 will actually mean
    # pre-major release
    # pylint: disable=W0141
    major, inter, minor = list(map(int, version.split(".")))
    numversion = major * 10000 + inter * 100 + minor
    numversion -= 1
    major = numversion // 10000
    inter = (numversion // 100) % 100
    minor = numversion % 100
    version = ".".join(map(str, [major, inter, minor]))

    now = datetime.datetime.today()
    release_day = str(now.day)
    release_month = months[now.month - 1]
    release_year = str(now.year)
    release_status = "beta"
    version += "." + revision

assert release_month in months  # Try to prevent typo's
release_month_nr = f"{months.index(release_month) + 1:02d}"
release_day_nr = f"{int(release_day):02d}"
date = f"{release_month} {release_day}, {release_year}"

name = "Task Coach"
description = "Your friendly task manager"
long_description = (
    "{name} is a free open source todo manager. It grew "
    "out of frustration about other programs not handling composite tasks well. "
    "In addition to flexible composite tasks, {name} has grown to include "
    "prerequisites, prioritizing, effort tracking, category tags, budgets, "
    "notes, and many other features. However, users are not forced to use all "
    "these features; {name} can be as simple or complex as you need it to be. "
    "{name} is available for Windows, Mac OS X, and GNU/Linux; and there is a "
    "companion iOS app.".format(name=name)
)
keywords = "task manager, todo list, pim, time registration, track effort"
author_first, author_last = "Frank", "Niessink"  # Needed for PAD file
author = f"{author_first} {author_last}, Jerome Laheurte, and Aaron Wolf"
author_unicode = (
    f"{author_first} {author_last}, Jérôme Laheurte, and Aaron Wolf"
)
author_email = "developers@taskcoach.org"

filename = name.replace(" ", "")
filename_lower = filename.lower()

url = "http://taskcoach.org/"  # Don't remove the trailing slash, other code is assuming it will be there
screenshot = f"{url}screenshots/Windows/0.71.2-Windows_XP-Tasks_categories_and_effort.png"
icon = f"{url}taskcoach.png"
pad = f"{url}pad.xml"
version_url = f"{url}version.txt"
message_url = f"{url}messages.txt"
download = f"{url}download.html"
dist_download_prefix = f"http://downloads.sourceforge.net/{filename_lower}"
faq_url = "https://answers.launchpad.net/taskcoach/+faqs"
sf_tracker_url = "https://sourceforge.net/tracker/"
bug_report_url = f"{sf_tracker_url}?func=add&group_id=130831&atid=719134"
known_bugs_url = f"{sf_tracker_url}?group_id=130831&atid=719134&status=1"
support_request_url = f"{sf_tracker_url}?group_id=130831&atid=719135"
feature_request_url = "http://taskcoach.uservoice.com"
translations_url = "https://translations.launchpad.net/taskcoach"
donate_url = f"{url}givesupport.html"
i18n_url = f"{url}i18n.html"

announcement_addresses = (
    "taskcoach@yahoogroups.com, python-announce-list@python.org"
)
bcc_announcement_addresses = "johnhaller@portableapps.com"

copyright = (
    f"Copyright (C) 2004-{release_year} {author}"  # pylint: disable=W0622
)
license_title = "GNU General Public License"
license_version = "3"
license_title_and_version = f"{license_title} version {license_version}"
license = f"{license_title_and_version} or any later version"  # pylint: disable=W0622
license_title_and_version_abbrev = f"GPLv{license_version}"
license_abbrev = f"{license_title_and_version_abbrev}+"
license_notice = """{name} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

{name} is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.""".format(
    name=name
)

license_notice_html = "<p>{}</p>".format(
    license_notice.replace("\n\n", "</p><p>")
)
license_notice_html = re.sub(
    r"<http([^>]*)>",
    r'<a href="http\1" target="_blank">http\1</a>',
    license_notice_html,
)

platform = "Any"
pythonversion = "2.6"
wxpythonversionnumber = "3.0.0.0"
wxpythonversion = f"{wxpythonversionnumber}-unicode"
twistedversionnumber = "10.0"
igraphversionnumber = "0.7"

languages = {
    "English (US)": (None, True),
    "English (AU)": ("en_AU", True),
    "English (CA)": ("en_CA", True),
    "English (GB)": ("en_GB", True),
    "Arabic": ("ar", False),
    "Basque": ("eu", False),
    "Belarusian": ("be", False),
    "Bosnian": ("bs", False),
    "Breton": ("br", False),
    "Bulgarian": ("bg", False),
    "Catalan": ("ca", False),
    "Chinese (Simplified)": ("zh_CN", False),
    "Chinese (Traditional)": ("zh_TW", False),
    "Czech": ("cs", True),
    "Danish": ("da", False),
    "Dutch": ("nl", True),
    "Esperanto": ("eo", False),
    "Estonian": ("et", False),
    "Finnish": ("fi", True),
    "French": ("fr", True),
    "Galician": ("gl", False),
    "German": ("de", True),
    "German (Low)": ("nds", False),
    "Greek": ("el", False),
    "Hebrew": ("he", False),
    "Hindi": ("hi", False),
    "Hungarian": ("hu", False),
    "Indonesian": ("id", False),
    "Italian": ("it", True),
    "Japanese": ("ja", False),
    "Korean": ("ko", False),
    "Latvian": ("lv", False),
    "Lithuanian": ("lt", False),
    "Marathi": ("mr", False),
    "Mongolian": ("mn", False),
    "Norwegian (Bokmal)": ("nb", False),
    "Norwegian (Nynorsk)": ("nn", False),
    "Occitan": ("oc", False),
    "Papiamento": ("pap", False),
    "Persian": ("fa", False),
    "Polish": ("pl", True),
    "Portuguese": ("pt", True),
    "Portuguese (Brazilian)": ("pt_BR", True),
    "Romanian": ("ro", True),
    "Russian": ("ru", True),
    "Slovak": ("sk", True),
    "Slovene": ("sl", False),
    "Spanish": ("es", True),
    "Swedish": ("sv", False),
    "Telugu": ("te", False),
    "Thai": ("th", False),
    "Turkish": ("tr", True),
    "Ukranian": ("uk", False),
    "Vietnamese": ("vi", False),
}
languages_list = ",".join(list(languages.keys()))


def __createDict(localsDict):
    """Provide the local variables as a dictionary for use in string
    formatting."""
    metaDict = {}  # pylint: disable=W0621
    for key in localsDict:
        if not key.startswith("__"):
            metaDict[key] = localsDict[key]
    return metaDict


metaDict = __createDict(locals())
