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
# futurize +1 ligne
# from builtins import object
import textwrap
import changetypes
import re


# Change (bugs fixed, features added, etc.) converters:

class ChangeConverter(object):
    def convert(self, change):
        result = self.preProcess(change.description)
        if hasattr(change, "url"):  # todo: 'url' -> 'urlpo' ?
            result += ' (%s)' % self.converturl(change.url)
        if change.changeIds:
            convertedids = self.convertchangeids(change)
            result += ' (%s)' % ', '.join(convertedids)
        return self.postprocess(result)

    def preProcess(self, changetobeconverted):
        return changetobeconverted

    def postprocess(self, convertedchange):
        return convertedchange

    def convertchangeids(self, change):
        # Shadows built-in name 'id'
        return [self.convertchangeid(change, id) for id in change.changeIds]

    def convertchangeid(self, change, changeid):
        return changeid

    def converturl(self, url):
        return url


class ChangeToTextConverter(ChangeConverter):
    def __init__(self):
        self._textWrapper = textwrap.TextWrapper(initial_indent='- ',
                                                 subsequent_indent='  ', width=78)
        # Regular expression to remove multiple spaces, except when on
        # the start of a line:
        self._multipleSpaces = re.compile(r'(?<!^) +', re.M)
        self._initialSpaces = re.compile(r'^( *)(.*)$')

    def postprocess(self, convertedchange):
        convertedchange = self._textWrapper.fill(convertedchange)
        # Somehow the text wrapper introduces multiple spaces within
        # lines, this is a workaround (preserving the initial spaces):

        lines = []

        for line in convertedchange.split('\n'):
            match = self._initialSpaces.match(line)
            lines.append(match.group(1) + self._multipleSpaces.sub(' ', match.group(2)))

        return '\n'.join(lines)

    def convertchangeid(self, change, changeid):
        return changeid if changeid.startswith('http') else 'SF#%s' % changeid


class ChangeToDebianConverter(ChangeToTextConverter):
    def __init__(self):
        super(ChangeToDebianConverter, self).__init__()
        self._textWrapper = textwrap.TextWrapper(initial_indent='  * ',
                                                 subsequent_indent='    ', width=78)

    def postprocess(self, convertedchange):
        return super(ChangeToDebianConverter, self).postProcess(convertedchange) + '\n'


class ChangeToHTMLConverter(ChangeConverter):
    LinkToSourceForge = '<a href="https://sourceforge.net/tracker/index.php?func=detail&aid=%%(' \
                        'id)s&group_id=130831&atid=%(atid)s">%%(id)s</a>'
    LinkToSourceForgeBugReport = LinkToSourceForge % {'atid': '719134'}
    LinkToSourceForgeBugReportv2 = '<a href="https://sourceforge.net/p/taskcoach/bugs/%(id)s/">%(id)s</a>'
    LinkToSourceForgeFeatureRequest = LinkToSourceForge % {'atid': '719137'}
    NoConversion = '%(id)s'

    def preProcess(self, changetobeconverted):
        changetobeconverted = re.sub('<', '&lt;', changetobeconverted)
        changetobeconverted = re.sub('>', '&gt;', changetobeconverted)
        return changetobeconverted

    def postprocess(self, convertedchange):
        list_of_url_and_text_fragments = re.split('(http://[^\s()]+[^\s().])', convertedchange)
        list_of_converted_urls_and_text_fragments = []
        for fragment in list_of_url_and_text_fragments:
            if fragment.startswith('http://'):
                fragment = self.converturl(fragment)
            list_of_converted_urls_and_text_fragments.append(fragment)
        convertedchange = ''.join(list_of_converted_urls_and_text_fragments)
        return '<li>%s</li>' % convertedchange

    def convertchangeid(self, change, changeid):
        template = self.NoConversion  # URL's will be converted in postProcess()
        if not changeid.startswith('http'):
            if isinstance(change, changetypes.Bugv2):
                template = self.LinkToSourceForgeBugReportv2
            elif isinstance(change, changetypes.Bug):
                template = self.LinkToSourceForgeBugReport
            elif isinstance(change, changetypes.Feature):
                template = self.LinkToSourceForgeFeatureRequest
        return template % {'id': changeid}

    def converturl(self, url):
        return '<a href="%s">%s</a>' % (url, url)


# Release converters:

class ReleaseConverter(object):
    def __init__(self):
        self._changeConverter = self.ChangeConverterClass()

    # @staticmethod ?
    def _add_s(listtocount):
        multiple = len(listtocount) > 1
        return dict(s='s' if multiple else '',
                    y='ies' if multiple else 'y')

    def convert(self, release, greeting=''):
        result = [self.summary(release, greeting)]
        if not greeting:
            result.insert(0, self.header(release))
        # Shadows built-in name 'list'
        for section, list in [('Team change%(s)s', release.teamChanges),
                              ('Bug%(s)s fixed', release.bugsFixed),
                              ('Feature%(s)s added', release.featuresAdded),
                              ('Feature%(s)s changed', release.featuresChanged),
                              ('Feature%(s)s removed', release.featuresRemoved),
                              ('Implementation%(s)s changed', release.implementationChanged),
                              ('Dependenc%(y)s changed', release.dependenciesChanged),
                              ('Distribution%(s)s changed', release.distributionsChanged),
                              ('Website change%(s)s', release.websiteChanges)]:
            if list:
                result.append(self.sectionheader(section, list))
                for change in list:
                    result.append(self._changeConverter.convert(change))
                result.append(self.sectionfooter(section, list))
        result = [line for line in result if line]
        return '\n'.join(result) + '\n\n'

    def header(self, release):
        return 'Release %s - %s' % (release.number, release.Date)

    def summary(self, release, greeting=''):
        return ' '.join([text for text in (greeting, release.summary) if text])

    def sectionheader(self, section, list):
        return '\n%s:' % (section % self._add_s(list))

    def sectionfooter(self, section, list):
        return ''


class ReleaseToTextConverter(ReleaseConverter):
    ChangeConverterClass = ChangeToTextConverter

    def summary(self, *args, **kwargs):
        summary = super(ReleaseToTextConverter, self).summary(*args, **kwargs)
        wrapper = textwrap.TextWrapper(initial_indent='',
                                       subsequent_indent='', width=78)
        multiplespaces = re.compile(r'(?<!^) +', re.M)
        summary = wrapper.fill(summary)
        # Somehow the text wrapper introduces multiple spaces within
        # lines, this is a workaround:
        summary = multiplespaces.sub(' ', summary)
        return summary


class ReleaseToDebianConverter(ReleaseConverter):
    ChangeConverterClass = ChangeToDebianConverter

    def summary(self, *args, **kwargs):
        return ''

    def header(self, release):
        return ''

    def sectionheader(self, section, list):
        return ''


class ReleaseToHTMLConverter(ReleaseConverter):
    ChangeConverterClass = ChangeToHTMLConverter

    def header(self, release):
        return '<h2>Release %s <small>%s</small></h2>' % (release.number, release.Date)

    def sectionheader(self, section, list):
        return super(ReleaseToHTMLConverter, self).sectionHeader(section,
                                     list) + '\n<ul>'

    def sectionfooter(self, section, list):
        return '</ul>'

    def summary(self, release, greeting=''):
        summarytext = super(ReleaseToHTMLConverter, self).summary(release)
        if summarytext:
            return '<p>%s</p>' % summarytext
        else:
            return ''
