# -*- coding: utf-8 -*-
# Ce fichier contient des tests unitaires pour la lecture de fichiers XML dans Task Coach.

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

Tests unitaires pour la lecture des fichiers XML dans Task Coach.

Ce module contient une série de cas de test vérifiant que les différentes versions du format XML
utilisé par Task Coach sont correctement prises en charge par le parseur XML (`persistence.XMLReader`).

Les tests couvrent :
- La rétrocompatibilité avec d'anciennes versions (v6 à v37)
- Le traitement des tâches, catégories, notes et efforts
- La gestion des pièces jointes, de la récurrence, des couleurs, des polices
- La lecture d'attributs comme `priority`, `reminder`, `completionDateTime`, etc.
"""

# from future import standard_library
import base64
import io
import logging
import os
import tempfile
import wx
from xml.parsers import expat
from xml.etree import ElementTree

# import lxml.etree
from ... import tctest
from taskcoachlib import persistence, config, operating_system
from taskcoachlib.domain import date, task

# standard_library.install_aliases()

log = logging.getLogger(__name__)


class XMLTemplateReaderTestCase(tctest.TestCase):
    """Tests pour la conversion d'expressions temporelles dans les modèles XML.

    Ce test vérifie que certaines expressions temporelles comme `Now()`, `Today()`,
    `Now().endOfDay()` ou `TimeDelta(...)` sont bien converties en chaînes lisibles.
    """

    def convert(self, old_format, now=date.Now):
        return persistence.TemplateXMLReader.convert_old_format(
            old_format, now
        )

    def testConvertNow(self):
        self.assertEqual("Now", self.convert("Now()"))

    def testConvertToday(self):
        self.assertEqual("00:00 AM Today", self.convert("Today()"))

    def testConvertTomorrow(self):
        self.assertEqual("11:59 PM Tomorrow", self.convert("Tomorrow()"))

    def testConvertEndOfDay(self):
        self.assertEqual("11:59 PM Today", self.convert("Now().endOfDay()"))

    def testConvertTomorrow2(self):
        self.assertEqual(
            "11:59 PM Tomorrow", self.convert("Now().endOfDay() + oneDay")
        )

    def testConvertNowAndPositiveTimeDelta(self):
        # self.assertEqual(
        #     "%d minutes from Now" % date.TimeDelta(2, 1861, 0).minutes(),
        #     self.convert("Now() + TimeDelta(2, 1861, 0)"),
        # )
        self.assertEqual(
            f"{int(date.TimeDelta(2, 1861, 0).minutes()):d} minutes from Now",
            self.convert("Now() + TimeDelta(2, 1861, 0)"),
        )

    def testConvertNowAndNegativeTimeDelta(self):
        # self.assertEqual(
        #     "%d minutes ago" % date.TimeDelta(2, 1861, 0).minutes(),
        #     self.convert("Now() - TimeDelta(2, 1861, 0)"),
        # )
        self.assertEqual(
            f"{int(date.TimeDelta(2, 1861, 0).minutes()):d} minutes ago",
            self.convert("Now() - TimeDelta(2, 1861, 0)"),
        )

    def testConvertTodayAndPositiveTimeDelta(self):
        now = date.Now()
        expectedDate = date.Now() + date.TimeDelta(17)
        expectedDateTime = date.DateTime(
            expectedDate.year, expectedDate.month, expectedDate.day
        )
        expectedMinutes = (expectedDateTime - now).minutes()
        actualMinutes = int(
            self.convert("Today() + TimeDelta(17)").split(" ")[0]
        )
        self.assertTrue(abs(actualMinutes - expectedMinutes) <= 1)

    def testConvertTodayAndZeroTimeDelta(self):
        now = date.Now()
        expectedMinutes = (now - now.startOfDay()).minutes()
        actualMinutes = int(
            self.convert("Today() + TimeDelta(0)").split(" ")[0]
        )
        self.assertTrue(abs(actualMinutes - expectedMinutes) <= 1)


class XMLReaderTestCase(tctest.TestCase):
    """Classe de base pour les tests de lecture XML.

    Fournit des utilitaires pour écrire des contenus XML simulés en mémoire, les lire
    via `persistence.XMLReader`, et extraire les éléments de plus haut niveau :
    - tâches
    - catégories
    - notes
    - configuration SyncML
    - GUID
    - changements (`changes`)
    """

    # Géré en amont :
    tskversion = "Subclass responsibility"

    def setUp(self):
        super().setUp()
        task.Task.settings = config.Settings(load=False)

    def writeAndRead(self, xml_contents):
        """Écrit une chaîne XML simulée dans un tampon mémoire, puis utilise XMLReader pour la lire."""
        # pylint: disable=W0201
        # Attributs :
        # Sortie de tampon d'écriture
        self.fd = io.StringIO()
        # self.fd = io.BytesIO()
        # Nom du fichier (inutile pour StringIO)
        self.fd.name = "testfile.tsk"
        # Classe pour lire le fichier
        # =persistence.XMLReader(io.StringIO())
        self.reader = persistence.XMLReader(self.fd)

        # print(f"XMLReadertest.writeAndRead: Création du tampon d'écriture all_xml pour xml_contents = {xml_contents}")
        all_xml = (
            "<?taskcoach release='whatever' "
            # 'tskversion="%d"?>\n' % self.tskversion + xml_contents
            # f"tskversion='{self.tskversion:d}'?>\n"
            f"tskversion='{self.tskversion:d}'?>"
            f"{xml_contents}"
        )
        # ).encode(encoding="utf-8")
        # print(f"XMLReadertest.writeAndRead: Essaie d'écrire all_xml={all_xml} dans self.fd={self.fd}")
        self.fd.write(all_xml)
        self.fd.seek(0)
        print(
            f"XMLReadertest.writeAndRead: résultat de write dans self.fd avant seek = {self.fd.read()}"
        )
        self.fd.seek(0)
        # return self.reader.read()
        the_return = self.reader.read()
        print(
            f"XMLReadertest.writeAndRead : Renvoie ce que read retourne = {the_return}"
        )
        return the_return

    def writeAndReadTasks(self, xml_contents):
        """Lit uniquement la section `<tasks>` depuis un contenu XML simulé."""
        # return self.writeAndRead(xml_contents)[0]
        contents = self.writeAndRead(xml_contents)[0]
        print(
            f"XMLReaderTestCase.writeAndReadTasks : Retourne la partie <tasks> : {contents}."
        )
        return contents

    def writeAndReadCategories(self, xml_contents):
        """Lit uniquement la section `<categories>` depuis un contenu XML simulé."""
        return self.writeAndRead(xml_contents)[1]

    def writeAndReadNotes(self, xml_contents):
        """Lit uniquement la section `<notes>` depuis un contenu XML simulé."""
        return self.writeAndRead(xml_contents)[2]

    def writeAndReadSyncMLConfig(self, xml_contents):
        """Lit uniquement la section `<>` depuis un contenu XML simulé."""
        return self.writeAndRead(xml_contents)[3]

    def writeAndReadGUID(self, xml_contents):
        """Lit uniquement la section `<guid>` depuis un contenu XML simulé."""
        return self.writeAndRead(xml_contents)[5]

    def writeAndReadTasksAndCategories(self, xml_contents):
        """Lit les sections `<tasks>` et `<categories>` d’un contenu XML simulé."""
        print(f"writeAndReadTasksAndCategories: xml_contents = {xml_contents}")
        tasks, categories, _, _, _, _ = self.writeAndRead(xml_contents)
        return tasks, categories

    def writeAndReadTasksAndCategoriesAndNotes(self, xml_contents):
        """Lit les sections `<tasks>`, `<categories>` et `<notes>` d’un contenu XML simulé."""
        tasks, categories, notes, _, _, _ = self.writeAndRead(xml_contents)
        return tasks, categories, notes

    def writeAndReadCategoriesAndNotes(self, xml_contents):
        """Lit les sections `<categories>` et `<notes>` d’un contenu XML simulé."""
        _, categories, notes, _, _, _ = self.writeAndRead(xml_contents)
        return categories, notes


class TempFileLockTest(XMLReaderTestCase):
    """Test de verrouillage temporaire de fichiers dans le cas des pièces jointes.

    Vérifie notamment que des fichiers temporaires sont bien créés et gérés sous Windows
    lors du traitement des pièces jointes (email en base64).
    """

    tskversion = 25

    def setUp(self):
        self.oldMkstemp = tempfile.mkstemp

        # def newMkstemp(*args, **kwargs):  # pragma: no cover
        #     handle, name = self.oldMkstemp(*args, **kwargs)
        #     self.__filename = name  # pylint: disable=W0201
        #     return handle, name

        # tempfile.mkstemp = newMkstemp
        tempfile.mkstemp = self.newMkstemp
        super().setUp()

    def newMkstemp(self, *args, **kwargs):  # pragma: no cover
        handle, name = self.oldMkstemp(*args, **kwargs)
        self.__filename = name  # pylint: disable=W0201
        return handle, name

    def tearDown(self):
        tempfile.mkstemp = self.oldMkstemp
        super().tearDown()

    def testLock(self):
        if os.name == "nt":  # pragma: no cover
            self.writeAndReadTasks(
                "<tasks>\n"
                '<task status="0">\n'
                '<attachment type="mail" status="0">\n'
                '<data extension="eml">{}</data>\n'
                "</attachment>\n"
                "</task>\n"
                "</tasks>\n".format(base64.encodestring("Data"))
            )
            try:
                os.remove(self.__filename)
                # os.remove(self.__filename + ".delta")
                os.remove(f"{self.__filename}.delta")
            except Exception:
                pass  # pylint: disable=W0702

            # self.assertTrue(os.path.exists(self.__filename))
            self.assert_(os.path.exists(self.__filename))


class XMLReaderVersion6Test(XMLReaderTestCase):
    """Tests pour le format XML version 6.

    Vérifie la robustesse du parseur sur des fichiers XML vides ou minimaux,
    ainsi que la gestion des éléments de base : tâches simples, catégories, etc.
    """

    tskversion = 6

    def testDescription(self):
        """Test si la description d'une tâche est bien lu."""
        tasks = self.writeAndReadTasks(f"""
        <tasks>
            <task description="%s" id="foo"/>
        </tasks>\n""" % "Description")
        # tasks = self.writeAndReadTasks(
        #     f"""
        # <tasks>
        #     <task description="{"Description"}" id="foo"/>
        # </tasks>\n"""
        # )
        print(f"XMLReaderVersion6Test.testDescription : tasks = {tasks}")
        self.assertEqual("Description", tasks[0].description())

    def testEffortDescription(self):
        tasks = self.writeAndReadTasks("""
            <tasks>
                <task id="foo">
                    <effort start="2004-01-01 10:00:00.123000"
                            stop="2004-01-01 10:30:00.123000"
                            description="Yo"/>
                </task>
            </tasks>""")
        self.assertEqual("Yo", tasks[0].efforts()[0].description())


class XMLReaderVersion8Test(XMLReaderTestCase):
    tskversion = 8

    def testReadTaskWithoutPriority(self):
        tasks = self.writeAndReadTasks('<tasks><task id="foo"/></tasks>')
        self.assertEqual(0, tasks[0].priority())


class XMLReaderVersion9Test(XMLReaderTestCase):
    tskversion = 9

    def testReadTaskWithoutId(self):
        tasks = self.writeAndReadTasks('<tasks><task id="foo"/></tasks>')
        self.assertTrue(tasks[0].id())


class XMLReaderVersion10Test(XMLReaderTestCase):
    tskversion = 10

    def testReadTaskWithoutFee(self):
        tasks = self.writeAndReadTasks('<tasks><task id="foo"/></tasks>')
        self.assertEqual(0, tasks[0].hourlyFee())
        self.assertEqual(0, tasks[0].fixedFee())


class XMLReaderVersion11Test(XMLReaderTestCase):
    tskversion = 11

    def testReadTaskWithoutReminder(self):
        tasks = self.writeAndReadTasks('<tasks><task id="foo"/></tasks>')
        self.assertEqual(date.DateTime(), tasks[0].reminder())


class XMLReaderVersion12Test(XMLReaderTestCase):
    tskversion = 12

    def testReadTaskWithoutMarkCompletedWhenAllChildrenCompletedSetting(self):
        tasks = self.writeAndReadTasks('<tasks><task id="foo"/></tasks>')
        self.assertEqual(
            None, tasks[0].shouldMarkCompletedWhenAllChildrenCompleted()
        )


class XMLReaderVersion13Test(XMLReaderTestCase):
    tskversion = 13

    def testOneCategory(self):
        tasks, categories = self.writeAndReadTasksAndCategories("""
        <tasks>
            <task id="1">
                <category>test</category>
            </task>
        </tasks>""")

        self.assertEqual("test", categories[0].subject())
        # self.assertEqual(set([tasks[0]]), categories[0].categorizables())
        self.assertEqual({tasks[0]}, categories[0].categorizables())
        # self.assertEqual(set([categories[0]]), tasks[0].categories())
        self.assertEqual({categories[0]}, tasks[0].categories())

    def testMultipleCategories(self):
        tasks, categories = self.writeAndReadTasksAndCategories("""
        <tasks>
            <task id="1">
                <category>test</category>
                <category>another</category>
                <category>yetanother</category>
            </task>
        </tasks>""")

        for category in categories:
            # self.assertEqual(set([tasks[0]]), category.categorizables())
            self.assertEqual({tasks[0]}, category.categorizables())
            self.assertTrue(category in tasks[0].categories())

    def testSubTaskWithCategories(self):
        tasks, categories = self.writeAndReadTasksAndCategories("""
            <tasks>
                <task id="1">
                    <category>test</category>
                    <task id="1.1">
                        <category>another</category>
                    </task>
                </task>
            </tasks>
            """)
        testCategory = categories[0]
        anotherCategory = categories[1]

        print(
            f"Catégorie 'test' contient : {[obj.id() for obj in testCategory.categorizables()]}"
        )
        print(
            f"Catégorie 'another' contient : {[obj.id() for obj in anotherCategory.categorizables()]}"
        )
        print(
            f"🔎 TEST - Catégorie de la sous-tâche après parsing : {tasks[0].children()[0].categories()}"
        )

        self.assertEqual("1", list(testCategory.categorizables())[0].id())
        self.assertEqual("1.1", list(anotherCategory.categorizables())[0].id())
        #                            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^
        # IndexError: list index out of range
        # self.assertEqual(set([testCategory]), tasks[0].categories())
        self.assertEqual({testCategory}, tasks[0].categories())
        # print(f"test : 🔍 DEBUG - Catégories attendues : {anotherCategory}")
        # print(f"test : 🔍 DEBUG - Catégories réelles : {tasks[0].children()[0].categories()}")
        # self.assertEqual(set([anotherCategory]), tasks[0].children()[0].categories())
        self.assertEqual(
            {anotherCategory}, tasks[0].children()[0].categories()
        )


class XMLReaderVersion14Test(XMLReaderTestCase):
    tskversion = 14

    def testEffortWithMilliseconds(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task>
                <effort start="2004-01-01 10:00:00.123000" 
                        stop="2004-01-01 10:30:00.123000"/>
            </task>
        </tasks>""")
        self.assertEqual(1, len(tasks[0].efforts()))
        self.assertEqual(date.TimeDelta(minutes=30), tasks[0].timeSpent())
        self.assertEqual(tasks[0], tasks[0].efforts()[0].task())


class XMLReaderVersion16Text(XMLReaderTestCase):
    tskversion = 16

    def testOneAttachmentCompat(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task>
                <attachment>whatever.tsk</attachment>
            </task>
        </tasks>""")
        self.assertEqual(
            ["whatever.tsk"],
            [att.location() for att in tasks[0].attachments()],
        )
        self.assertEqual(
            ["whatever.tsk"], [att.subject() for att in tasks[0].attachments()]
        )

    def testTwoAttachmentsCompat(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task>
                <attachment>whatever.tsk</attachment>
                <attachment>another.txt</attachment>
            </task>
        </tasks>""")
        self.assertEqual(
            ["whatever.tsk", "another.txt"],
            [att.location() for att in tasks[0].attachments()],
        )
        self.assertEqual(
            ["whatever.tsk", "another.txt"],
            [att.subject() for att in tasks[0].attachments()],
        )

    # TODO : A revoir :
    def testOneAttachment(self):
        """
        Il teste le chargement d'une tâche avec une seule pièce jointe à partir d'un fichier XML.
        Le test utilise une méthode writeAndReadTasks qui écrit du contenu XML simulé en mémoire et le lit via XMLReader.
        Il vérifie que la tâche et sa pièce jointe sont correctement chargées.
        """
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task>
                <attachment>FILE:whatever.tsk</attachment>
            </task>
        </tasks>""")
        self.assertEqual(
            ["whatever.tsk"],
            [att.location() for att in tasks[0].attachments()],
        )
        # self.assertEqual(
        #     ["FILE:whatever.tsk"], [att.subject() for att in tasks[0].attachments()]
        # )

    def testTwoAttachments(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task>
                <attachment>FILE:whatever.tsk</attachment>
                <attachment>FILE:another.txt</attachment>
            </task>
        </tasks>""")
        self.assertEqual(
            ["whatever.tsk", "another.txt"],
            [att.location() for att in tasks[0].attachments()],
        )
        self.assertEqual(
            ["whatever.tsk", "another.txt"],
            [att.subject() for att in tasks[0].attachments()],
        )


# There's no XMLReaderVersion17Test because the only difference between version
# 17 and 18 is the addition of an optional color attribute to categories in
# version 18. So the tests for version 18 test version 17 as well.


class XMLReaderVersion18Test(XMLReaderTestCase):
    tskversion = 18

    def testLastModificationTime(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task lastModificationTime="2004-01-01 10:00:00"/>
        </tasks>""")
        self.assertEqual(1, len(tasks))  # Ignore lastModificationTime


class XMLReaderVersion19Test(XMLReaderTestCase):
    tskversion = 19  # New in release 0.69.0?

    def testDailyRecurrence(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task recurrence="daily"/>
        </tasks>""")
        self.assertEqual("daily", tasks[0].recurrence().unit)

    def testWeeklyRecurrence(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task recurrence="weekly"/>
        </tasks>""")
        self.assertEqual("weekly", tasks[0].recurrence().unit)

    def testMonthlyRecurrence(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task recurrence="monthly"/>
        </tasks>""")
        self.assertEqual("monthly", tasks[0].recurrence().unit)

    def testRecurrenceCount(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task recurrenceCount="10"/>
        </tasks>""")
        self.assertEqual(10, tasks[0].recurrence().count)

    def testMaxRecurrenceCount(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task maxRecurrenceCount="10"/>
        </tasks>""")
        self.assertEqual(10, tasks[0].recurrence().max)

    def testRecurrenceFrequency(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task recurrenceFrequency="3"/>
        </tasks>""")
        self.assertEqual(3, tasks[0].recurrence().amount)


class XMLReaderVersion20Test(XMLReaderTestCase):
    """Tests pour le format XML version 20 (introduit en release 0.71.0).

    Vérifie la robustesse du parseur sur des fichiers XML vides ou minimaux,
    ainsi que la gestion des éléments de base : tâches simples, catégories, etc.
    """

    tskversion = 20  # New in release 0.71.0

    def testReadEmptyStream(self):
        """
        Teste le comportement du lecteur XML quand le fichier est vide.
        Au lieu de s'attendre à une exception, le test vérifie maintenant que reader.read() retourne bien des valeurs vides :

        tasks, categories, notes doivent être des listes vides.
        syncml_config et guid doivent être None.
        changes doit être un dictionnaire vide {}.

        Returns :

        """
        reader = persistence.XMLReader(io.StringIO())
        # reader = persistence.XMLReader(io.BytesIO())
        try:
            # reader.read()
            # self.fail("Expected ExpatError or ParseError")  # pragma: no cover
            tasks, categories, notes, syncml_config, changes, guid = (
                reader.read()
            )
            self.assertEqual(tasks, [])
            self.assertEqual(categories, [])
            self.assertEqual(notes, [])
            self.assertIsNone(syncml_config)
            self.assertEqual(changes, {})
            self.assertIsNone(guid)
        except expat.ExpatError:
            # pass  # pragma: no cover
            self.fail("Unexpected ExpatError")  # pragma: no cover
        except ElementTree.ParseError:
            # pass  # pragma: no cover
            self.fail("Unexpected ParseError")  # pragma: no cover

    def testNoTasksAndNoCategories(self):
        tasks, categories, notes = self.writeAndReadTasksAndCategoriesAndNotes(
            "<tasks/>\n"
        )
        self.assertEqual(([], [], []), (tasks, categories, notes))

    def testOneTask(self):
        tasks = self.writeAndReadTasks("<tasks><task/></tasks>\n")
        self.assertEqual(1, len(tasks))
        self.assertEqual("", tasks[0].subject())

    def testTwoTasks(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task subject="1"/>
            <task subject="2"/>
        </tasks>\n""")
        self.assertEqual(2, len(tasks))
        self.assertEqual("1", tasks[0].subject())
        self.assertEqual("2", tasks[1].subject())

    def testOneTask_Subject(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task subject="Yo"/>
        </tasks>\n""")
        self.assertEqual("Yo", tasks[0].subject())

    def testOneTask_UnicodeSubject(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task subject="???"/>
        </tasks>\n""")
        self.assertEqual("???", tasks[0].subject())

    def testBudget(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task budget="4:10:10"/>
        </tasks>\n""")
        self.assertEqual(
            date.TimeDelta(hours=4, minutes=10, seconds=10), tasks[0].budget()
        )

    def testBudget_NoBudget(self):
        tasks = self.writeAndReadTasks("<tasks><task/></tasks>\n")
        self.assertEqual(date.TimeDelta(), tasks[0].budget())

    def testDescription(self):
        description = "Description\nline 2"
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task>
                <description>%s</description>
            </task>
        </tasks>\n""" % description)
        self.assertEqual(description, tasks[0].description())

    def testNoChildren(self):
        tasks = self.writeAndReadTasks("<tasks><task/></tasks>\n")
        self.assertFalse((tasks[0].children()))

    def testChild(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task>
                <task/>
            </task>
        </tasks>\n""")
        self.assertEqual(1, len(tasks[0].children()))
        self.assertEqual(1, len(tasks))

    def testChildren(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task>
                <task/>
                <task/>
            </task>
        </tasks>\n""")
        self.assertEqual(2, len(tasks[0].children()))
        self.assertEqual(1, len(tasks))

    def testGrandchild(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task>
                <task>
                    <task/>
                </task>
            </task>
        </tasks>\n""")
        self.assertEqual(1, len(tasks))
        parent = tasks[0]
        self.assertEqual(1, len(parent.children()))
        self.assertEqual(1, len(parent.children()[0].children()))

    def testEffort(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task>
                <effort start="2004-01-01 10:00:00"
                        stop="2004-01-01 10:30:00"/>
            </task>
        </tasks>""")
        self.assertEqual(1, len(tasks[0].efforts()))
        self.assertEqual(date.TimeDelta(minutes=30), tasks[0].timeSpent())
        self.assertEqual(tasks[0], tasks[0].efforts()[0].task())

    def testChildEffort(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task>
                <task>
                    <effort start="2004-01-01 10:00:00"
                            stop="2004-01-01 10:30:00"/>
                </task>
            </task>
        </tasks>""")
        child = tasks[0].children()[0]
        self.assertEqual(1, len(child.efforts()))
        self.assertEqual(date.TimeDelta(minutes=30), child.timeSpent())
        self.assertEqual(child, child.efforts()[0].task())

    def testEffortDescription(self):
        description = "Description\nLine 2"
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task>
                <effort start="2004-01-01 10:00:00">
                    <description>%s</description>
                </effort>
            </task>
        </tasks>""" % description)
        self.assertEqual(description, tasks[0].efforts()[0].description())

    def testActiveEffort(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task>
                <effort start="2004-01-01 10:00:00"/>
            </task>
        </tasks>""")
        self.assertEqual(1, len(tasks[0].efforts()))
        self.assertTrue(tasks[0].isBeingTracked())

    def testPriority(self):
        tasks = self.writeAndReadTasks('<tasks><task priority="5"/></tasks>')
        self.assertEqual(5, tasks[0].priority())

    def testTaskId(self):
        tasks = self.writeAndReadTasks('<tasks><task id="xyz"/></tasks>')
        self.assertEqual("xyz", tasks[0].id())

    def testTaskColor(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task color="(255, 0, 0, 255)"/>
        </tasks>""")
        self.assertEqual(wx.RED, tasks[0].backgroundColor())

    def testHourlyFee(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task hourlyFee="100"/>
            <task hourlyFee="5.5"/>
        </tasks>""")
        self.assertEqual(100, tasks[0].hourlyFee())
        self.assertEqual(5.5, tasks[1].hourlyFee())

    def testFixedFee(self):
        tasks = self.writeAndReadTasks(
            '<tasks><task fixedFee="240.50"/></tasks>'
        )
        self.assertEqual(240.5, tasks[0].fixedFee())

    def testNoReminder(self):
        tasks = self.writeAndReadTasks(
            '<tasks><task reminder="None"/></tasks>'
        )
        self.assertEqual(date.DateTime(), tasks[0].reminder())

    def testReminder(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task reminder="2004-01-01 10:00:00"/>
        </tasks>""")
        self.assertEqual(
            date.DateTime(2004, 1, 1, 10, 0, 0, 0), tasks[0].reminder()
        )

    def testMarkCompletedWhenAllChildrenCompletedSetting_True(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task shouldMarkCompletedWhenAllChildrenCompleted="True"/>
        </tasks>""")
        self.assertEqual(
            True, tasks[0].shouldMarkCompletedWhenAllChildrenCompleted()
        )

    def testMarkCompletedWhenAllChildrenCompletedSetting_False(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task shouldMarkCompletedWhenAllChildrenCompleted="False"/>
        </tasks>""")
        self.assertEqual(
            False, tasks[0].shouldMarkCompletedWhenAllChildrenCompleted()
        )

    def testMarkCompletedWhenAllChildrenCompletedSetting_None(self):
        tasks = self.writeAndReadTasks("<tasks><task/></tasks>")
        self.assertEqual(
            None, tasks[0].shouldMarkCompletedWhenAllChildrenCompleted()
        )

    def testTaskWithoutAttachments(self):
        tasks = self.writeAndReadTasks("<tasks><task/></tasks>")
        self.assertEqual([], tasks[0].attachments())

    def testNoteWithoutAttachments(self):
        notes = self.writeAndReadNotes("<tasks><note/></tasks>")
        self.assertEqual([], notes[0].attachments())

    def testCategoryWithoutAttachments(self):
        categories = self.writeAndReadCategories("<tasks><category/></tasks>")
        self.assertEqual([], categories[0].attachments())

    def testTaskWithOneAttachment(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task>
                <attachment type="file">
                    <description>whatever.tsk</description>
                    <data>whateverdata.tsk</data>
                </attachment>
            </task>
        </tasks>""")
        self.assertEqual(
            [
                os.path.join(
                    os.getcwd(), "testfile_attachments", "whateverdata.tsk"
                )
            ],
            [att.location() for att in tasks[0].attachments()],
        )
        self.assertEqual(
            ["whatever.tsk"], [att.subject() for att in tasks[0].attachments()]
        )

    def testNoteWithOneAttachment(self):
        notes = self.writeAndReadNotes("""
        <tasks>
            <note>
                <attachment type="file">
                    <description>whatever.tsk</description>
                    <data>whateverdata.tsk</data>
                </attachment>
            </note>
        </tasks>""")
        self.assertEqual(
            [
                os.path.join(
                    os.getcwd(), "testfile_attachments", "whateverdata.tsk"
                )
            ],
            [att.location() for att in notes[0].attachments()],
        )
        self.assertEqual(
            ["whatever.tsk"], [att.subject() for att in notes[0].attachments()]
        )

    def testCategoryWithOneAttachment(self):
        categories = self.writeAndReadCategories("""
        <tasks>
            <category>
                <attachment type="file">
                    <description>whatever.tsk</description>
                    <data>whateverdata.tsk</data>
                </attachment>
            </category>
        </tasks>""")
        self.assertEqual(
            [
                os.path.join(
                    os.getcwd(), "testfile_attachments", "whateverdata.tsk"
                )
            ],
            [att.location() for att in categories[0].attachments()],
        )
        self.assertEqual(
            ["whatever.tsk"],
            [att.subject() for att in categories[0].attachments()],
        )

    def testTaskWithTwoAttachments(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task>
                <attachment type="file">
                   <description>whatever.tsk</description>
                   <data>whateverdata.tsk</data>
                </attachment>
                <attachment type="file">
                    <description>another.txt</description>
                    <data>anotherdata.txt</data>
                </attachment>
            </task>
        </tasks>""")
        self.assertEqual(
            [
                os.path.join(
                    os.getcwd(), "testfile_attachments", "whateverdata.tsk"
                ),
                os.path.join(
                    os.getcwd(), "testfile_attachments", "anotherdata.txt"
                ),
            ],
            [att.location() for att in tasks[0].attachments()],
        )
        self.assertEqual(
            ["whatever.tsk", "another.txt"],
            [att.subject() for att in tasks[0].attachments()],
        )

    def testOneCategory(self):
        categories = self.writeAndReadCategories(
            '<tasks><category subject="cat"/></tasks>'
        )
        self.assertEqual("cat", categories[0].subject())

    def testTwoCategories(self):
        categories = self.writeAndReadCategories("""
        <tasks>
            <category subject="cat1"/>
            <category subject="cat2"/>
        </tasks>""")
        self.assertEqual(
            ["cat1", "cat2"], [category.subject() for category in categories]
        )

    def testCategoryId(self):
        categories = self.writeAndReadCategories("""
        <tasks>
            <category id="catId"/>
        </tasks>""")
        self.assertEqual("catId", categories[0].id())

    def testCategoryWithDescription(self):
        categories = self.writeAndReadCategories("""
        <tasks>
            <category subject="cat">
                <description>Description</description>
            </category>
        </tasks>""")
        self.assertEqual("Description", categories[0].description())

    def testCategoryColor(self):
        categories = self.writeAndReadCategories("""
        <tasks>
            <category subject="cat" color="(255, 0, 0, 255)"/>
        </tasks>""")
        self.assertEqual(wx.RED, categories[0].backgroundColor())

    def testOneTaskWithCategory(self):
        tasks, categories = self.writeAndReadTasksAndCategories("""
        <tasks>
            <category subject="cat" categorizables="1"/>
            <task id="1"/>
        </tasks>""")
        self.assertEqual(set(tasks), categories[0].categorizables())

    def testTwoRecursiveCategories(self):
        categories = self.writeAndReadCategories("""
        <tasks>
            <category subject="cat1">
                <category subject="cat1.1"/>
            </category>
        </tasks>""")
        self.assertEqual("cat1.1", categories[0].children()[0].subject())

    def testRecursiveCategoriesNotInResultList(self):
        """
        Ce test vérifie que lorsqu'on lui donne une structure hiérarchique de
        catégories, seules les catégories de niveau supérieur sont incluses
        dans la liste de résultats et les catégories imbriquées ne le sont pas.
        Ce comportement peut être important pour garantir que seules les
        catégories directes sont prises en compte dans certaines opérations
        ou vues.

        Il est conçu pour tester une fonctionnalité spécifique liée à la gestion des catégories, probablement dans un contexte de gestion de tâches ou organisationnel. Voici un aperçu de ce que fait le code :
        Définition de la méthode : la méthode testRecursiveCategoriesNotInResultList est définie.
        Configuration : la méthode utilise une fonction d'assistance writeAndReadCategories pour traiter une chaîne de données XML. Ces données XML représentent une structure hiérarchique de catégories :
        Il existe un élément racine <tasks>.
        À l'intérieur de <tasks>, il y a un élément <category> avec l'attribut subject="cat1".
        Imbriqué dans cette catégorie se trouve un autre élément <category> avec l'attribut subject="cat1.1".

        Appel de fonction : La fonction writeAndReadCategories est appelée avec la chaîne XML comme argument. Cette fonction est censée traiter le XML et renvoyer une liste de catégories. L'implémentation exacte de writeAndReadCategories n'est pas fournie, mais elle analyse probablement le XML et renvoie une liste d'objets ou de représentations de catégorie.

        Assertion: le test utilise self.assertEqual(1, len(categories)) pour affirmer que la longueur de la liste des catégories est 1. Cela implique que le test s'attend à ce que la fonction writeAndReadCategories renvoie uniquement la catégorie de niveau supérieur (cat1) et n'inclut pas la catégorie imbriquée (cat1.1) dans la liste de résultats.
        """
        categories = self.writeAndReadCategories("""
        <tasks>
            <category subject="cat1">
                <category subject="cat1.1"/>
            </category>
        </tasks>""")
        # Ne doit récupérer que les catégories de niveau supérieur root
        self.assertEqual(1, len(categories))

    def testRecursiveCategoriesWithTwoTasks(self):
        """Test récursivement des catégories avec deux tâches.

        Ce code est un test unitaire qui vérifie la bonne association des tâches avec des catégories dans une structure XML hiérarchique. Voici une explication détaillée de ce que fait le code :

        Configuration : l'extrait de code fait partie d'une méthode de test qui utilise la fonction writeAndReadTasksAndCategories. Cette fonction est chargée de traiter une chaîne XML donnée et de renvoyer deux listes : une pour les tâches et une autre pour les catégories.
        Structure XML : La chaîne XML fournie à writeAndReadTasksAndCategories représente une structure hiérarchique :
            Il existe un élément racine <tasks>.
            À l'intérieur de <tasks>, il y a un élément <category> avec l'attribut subject="cat1". Cette catégorie a un attribut catégorisable défini sur "1", indiquant qu'elle est associée à la tâche ayant id="1".
            Imbriqué dans cette catégorie se trouve un autre<category> élément avec l'attribut subject="cat1.1". Cette sous-catégorie a un attribut catégorisable défini sur "2", indiquant qu'elle est associée à la tâche ayant id="2".
            Deux éléments <task> sont définis respectivement avec subject="task1" et subject="task2", et id="1" et id="2".
        Appel de fonction : la fonction writeAndReadTasksAndCategories traite le XML et renvoie deux listes : tâches et catégories. La liste des tâches contient les objets de tâche et la liste des catégories contient les objets de catégorie.
        Assertions:
        self.assertEqual(tasks[0], list(categories[0].categorizings())[0]) : Cette assertion vérifie que la première tâche (task1) est correctement associée à la première catégorie (cat1). La méthode catégorisables() de la catégorie renvoie une liste de tâches associées, et le test vérifie que la première tâche de cette liste est task1.
        self.assertEqual(tasks[1], list(categories[0].children()[0].categorizings())[0]) : Cette assertion vérifie que la deuxième tâche (task2) est correctement associée à la sous-catégorie (cat1.1). La méthode children() de la catégorie renvoie une liste de sous-catégories et le test vérifie que la première tâche de la liste categorizable() de la première sous-catégorie est la tâche2.

        En résumé, ce test garantit que les tâches sont correctement associées à leurs catégories et sous-catégories respectives en fonction de l'attribut catégorisable dans la structure XML.
        """
        tasks, categories = self.writeAndReadTasksAndCategories("""
        <tasks>
            <category subject="cat1" categorizables="1">
                <category subject="cat1.1" categorizables="2"/>
            </category>
            <task subject="task1" id="1"/>
            <task subject="task2" id="2"/>
        </tasks>""")

        self.assertEqual(tasks[0], list(categories[0].categorizables())[0])
        self.assertEqual(
            tasks[1], list(categories[0].children()[0].categorizables())[0]
        )

    def testSubtaskCategory(self):
        tasks, categories = self.writeAndReadTasksAndCategories("""
        <tasks>
            <category subject="cat1" categorizables="1.1"/>
            <task subject="task1" id="1">
                <task subject="task2" id="1.1"/>
            </task>
        </tasks>""")
        self.assertEqual(
            tasks[0].children()[0], list(categories[0].categorizables())[0]
        )

    def testFilteredCategory(self):
        categories = self.writeAndReadCategories("""
        <tasks>
            <category filtered="True" subject="category"/>
        </tasks>""")
        self.assertTrue(categories[0].isFiltered())

    def testCategoryWithDeletedTasks(self):
        """There's a bug in release 0.61.5 that causes the task file to contain
        references to deleted tasks. Ignore these when loading the task
        file."""
        categories = self.writeAndReadCategories("""
        <tasks>
            <category subject="cat" tasks="some_task_id"/>
        </tasks>""")
        self.assertFalse(categories[0].categorizables())

    def testNote(self):
        notes = self.writeAndReadNotes("""
        <tasks>
            <note/>
        </tasks>""")
        self.assertTrue(notes)

    def testNoteSubject(self):
        notes = self.writeAndReadNotes("""
        <tasks>
            <note subject="Note"/>
        </tasks>""")
        self.assertEqual("Note", notes[0].subject())

    def testNoteDescription(self):
        notes = self.writeAndReadNotes("""
        <tasks>
            <note>
                <description>Description</description>
            </note>
        </tasks>""")
        self.assertEqual("Description", notes[0].description())

    def testNoteChild(self):
        notes = self.writeAndReadNotes("""
        <tasks>
            <note>
                <note/>
            </note>
        </tasks>""")
        self.assertEqual(1, len(notes[0].children()))

    def testNoteChildWithAttachment(self):
        notes = self.writeAndReadNotes("""
        <tasks>
            <note>
                <note>
                    <attachment type="file">
                       <description>whatever.tsk</description>
                       <data>whateverdata.tsk</data>
                    </attachment>
                </note>
            </note>
        </tasks>""")
        self.assertEqual(
            [
                os.path.join(
                    os.getcwd(), "testfile_attachments", "whateverdata.tsk"
                )
            ],
            [att.location() for att in notes[0].children()[0].attachments()],
        )
        self.assertEqual(
            ["whatever.tsk"],
            [att.subject() for att in notes[0].children()[0].attachments()],
        )

    def testNoteCategory(self):
        categories, notes = self.writeAndReadCategoriesAndNotes("""
        <tasks>
            <note id="noteId" subject="Note"/>
            <category categorizables="noteId" subject="Category"/>
        </tasks>""")
        self.assertEqual(notes[0], list(categories[0].categorizables())[0])

    def testNoteId(self):
        notes = self.writeAndReadNotes("""
        <tasks>
            <note id="noteId"/>
        </tasks>""")
        self.assertEqual("noteId", notes[0].id())

    def testNoteColor(self):
        notes = self.writeAndReadNotes("""
        <tasks>
            <note color="(255, 0, 0, 255)"/>
        </tasks>""")
        self.assertEqual(wx.RED, notes[0].backgroundColor())

    def testNoRecurrence(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task/>
        </tasks>""")
        self.assertFalse(tasks[0].recurrence())

    def testDailyRecurrence(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task><recurrence unit="daily"/></task>
        </tasks>""")
        self.assertEqual("daily", tasks[0].recurrence().unit)

    def testWeeklyRecurrence(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task><recurrence unit="weekly"/></task>
        </tasks>""")
        self.assertEqual("weekly", tasks[0].recurrence().unit)

    def testRecurrenceAmount(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task><recurrence unit="daily" amount="2"/></task>
        </tasks>""")
        self.assertEqual(2, tasks[0].recurrence().amount)

    def testRecurrenceMax(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task><recurrence unit="daily" max="2"/></task>
        </tasks>""")
        self.assertEqual(2, tasks[0].recurrence().max)

    def testRecurrenceCount(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task><recurrence unit="daily" count="2"/></task>
        </tasks>""")
        self.assertEqual(2, tasks[0].recurrence().count)

    def testRecurrenceSameWeekday(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task><recurrence unit="daily" sameWeekday="True"/></task>
        </tasks>""")
        self.assertTrue(tasks[0].recurrence().sameWeekday)

    def testTaskWithNote(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task>
                <note/>
            </task>
        </tasks>""")
        self.assertEqual(1, len(tasks[0].notes()))

    def testTaskWithNotes(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task>
                <note/><note/>
            </task>
        </tasks>""")
        self.assertEqual(2, len(tasks[0].notes()))

    def testTaskWithNestedNotes(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task>
                <note>
                    <note/>
                </note>
            </task>
        </tasks>""")
        self.assertEqual(1, len(tasks[0].notes()[0].children()))

    def testTaskNotesDontGetAddedToOverallNotesList(self):
        notes = self.writeAndReadNotes("""
        <tasks>
            <task>
                <note/>
            </task>
        </tasks>""")
        self.assertFalse(notes)

    def testCategoryWithNote(self):
        categories = self.writeAndReadCategories("""
            <tasks>
                <category>
                    <note/>
                </category>
            </tasks>""")
        self.assertEqual(1, len(categories[0].notes()))

    def testCategoryWithNotes(self):
        categories = self.writeAndReadCategories("""
            <tasks>
                <category>
                    <note/><note/>
                </category>
            </tasks>""")
        self.assertEqual(2, len(categories[0].notes()))

    def testCategoryWithNestedNotes(self):
        categories = self.writeAndReadCategories("""
            <tasks>
                <category>
                    <note>
                        <note/>
                    </note>
                </category>
            </tasks>""")
        self.assertEqual(1, len(categories[0].notes()[0].children()))

    def testCategoryNotesDontGetAddedToOverallNotesList(self):
        notes = self.writeAndReadNotes("""
        <tasks>
            <category>
                <note/>
            </category>
        </tasks>""")
        self.assertFalse(notes)

    def testTaskExpansion(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task expandedContexts="('None',)"/>
        </tasks>""")
        self.assertTrue(tasks[0].isExpanded())

    def testTaskExpansion_MultipleContexts(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task expandedContexts="('None','Test')"/>
        </tasks>""")
        self.assertTrue(tasks[0].isExpanded(context="Test"))

    def testCategoryExpansion(self):
        categories = self.writeAndReadCategories("""
        <tasks>
            <category expandedContexts="('None',)"/>
        </tasks>""")
        self.assertTrue(categories[0].isExpanded())

    def testNoteExpansion(self):
        notes = self.writeAndReadNotes("""
        <tasks>
            <note expandedContexts="('None',)"/>
        </tasks>""")
        self.assertTrue(notes[0].isExpanded())


class XMLReaderVersion21Test(XMLReaderTestCase):
    tskversion = 21  # New in release 0.71.0

    def testAttachmentLocation(self):
        categories = self.writeAndReadCategories("""
        <tasks>
            <category>
                <attachment type="file" location="location">
                   <description>description</description>
                </attachment>
            </category>
        </tasks>""")
        self.assertEqual(
            ["location"],
            [
                os.path.split(att.location())[-1]
                for att in categories[0].attachments()
            ],
        )


class XMLReaderVersion22Test(XMLReaderTestCase):
    tskversion = 22

    def testStatus(self):
        tasks = self.writeAndReadTasks(
            '<tasks><task subject="Task" status="2"></task></tasks>'
        )
        # print(f"XMLReaderversion22test.testStatus : DEBUG: Type de status retourné: {type(tasks[0].status())}, Valeur: {tasks[0].status()}")
        # print(f"XMLReaderversion22test.testStatus : DEBUG: getStatus() avant test = {tasks[0].getStatus()} ({type(tasks[0].getStatus())})")

        self.assertEqual(2, tasks[0].getStatus())
        # self.assertEqual(2, tasks[0].status())
        # self.assertEqual(mod_status.completed, tasks[0].status())


class XMLReaderVersion23Test(XMLReaderTestCase):
    tskversion = 23

    def testDescription(self):
        tasks = self.writeAndReadTasks(
            '<tasks><task subject="Task" status="0">'
            "<description>\nDescription\n</description>"
            "</task></tasks>"
        )
        # self.assertEqual("\nDescription\n", tasks[0].description())
        self.assertEqual("Description", tasks[0].description())

    def testAttachmentData(self):
        # tasks = self.writeAndReadTasks(
        #     '<tasks>\n<task status="0">\n'
        #     '<attachment type="mail" status="0">\n'
        #     '<data extension="eml">%s</data>\n'
        #     "</attachment>\n</task>\n</tasks>\n" % base64.encodestring("Data")
        # )
        # tasks = self.writeAndReadTasks(
        #     '<tasks>\n<task status="0">\n'
        #     '<attachment type="mail" status="0">\n'
        #     '<data extension="eml">%s</data>\n'
        #     "</attachment>\n</task>\n</tasks>\n" % base64.encodebytes("Data".encode("utf-8"))
        #
        # )
        tasks = self.writeAndReadTasks(
            '<tasks>\n<task status="0">\n'
            '<attachment type="mail" status="0">\n'
            '<data extension="eml">%s</data>\n'
            "</attachment>\n</task>\n</tasks>\n"
            % base64.b64encode(b"Data").decode("utf-8")
        )
        self.assertEqual(
            b"Data", tasks[0].attachments()[0].data()
        )  # test avec bytes
        # self.assertEqual("Data", tasks[0].attachments()[0].data().decode("utf-8"))  # pour tester avec str

    def testGUID(self):
        guid = self.writeAndReadGUID("<tasks><guid>GUID</guid></tasks>")
        self.assertEqual("GUID", guid)

    def testSyncMLConfig(self):
        syncmlConfig = self.writeAndReadSyncMLConfig(
            '<tasks><syncml><property name="name">value</property></syncml></tasks>'
        )
        self.assertEqual(
            "value",
            syncmlConfig.get(
                "name",
            ),
        )


class XMLReaderVersion24Test(XMLReaderTestCase):
    tskversion = 24  # New in release 0.72.9

    # tskversion 24 introduces newlines so that the XML is not on one long
    # line anymore. We have to be sure not to introduce new lines in
    # text nodes though.

    def testDescription(self):
        tasks = self.writeAndReadTasks(
            '<tasks>\n<task subject="Task" status="0">\n'
            "<description>\nDescription\n</description>\n"
            "</task>\n</tasks>\n"
        )
        self.assertEqual("Description", tasks[0].description())

    def testAttachmentData(self):
        # tasks = self.writeAndReadTasks(
        #     '<tasks>\n<task status="0">\n'
        #     '<attachment type="mail" status="0">\n'
        #     '<data extension="eml">\n%s\n</data>\n'
        #     "</attachment>\n</task>\n</tasks>\n" % base64.encodestring("Data")
        # )
        # self.assertEqual("Data", tasks[0].attachments()[0].data())
        tasks = self.writeAndReadTasks(
            '<tasks>\n<task status="0">\n'
            '<attachment type="mail" status="0">\n'
            '<data extension="eml">\n%s\n</data>\n'
            "</attachment>\n</task>\n</tasks>\n"
            % base64.b64encode(b"Data").decode("utf-8")
        )
        self.assertEqual(
            b"Data", tasks[0].attachments()[0].data()
        )  # test avec bytes
        # self.assertEqual("Data", tasks[0].attachments()[0].data().decode("utf-8"))  # pour tester avec str

    def testGUID(self):
        guid = self.writeAndReadGUID(
            "<tasks>\n<guid>\nGUID\n</guid>\n</tasks>"
        )
        self.assertEqual("GUID", guid)

    def testSyncMLConfig(self):
        syncmlConfig = self.writeAndReadSyncMLConfig(
            "<tasks>\n<syncml>\n"
            '<property name="name">\nvalue\n</property>\n'
            "</syncml>\n</tasks>\n"
        )
        self.assertEqual(
            "value",
            syncmlConfig.get(
                "name",
            ),
        )

    def testSyncMLConfigWithNewLinesInXMLNodes(self):
        """Release 0.72.9 (and earlier?) had a bug where tags in the syncml
        config information would be split across multiple lines. Fixed in
        release 0.72.10."""
        expectedGUID = "0000011d209a4b6c3f9f7c32000a00b100240032"
        actualGUID = self.writeAndReadGUID(
            "<tasks>\n<syncml><TaskCoach-\n"
            "0000011d209a4b6c3f9f7c32000a00b100240032\n"
            "><spds><sources><TaskCoach-\n"
            "0000011d209a4b6c3f9f7c32000a00b100240032\n"
            ".Tasks/><TaskCoach-\n"
            "0000011d209a4b6c3f9f7c32000a00b100240032\n"
            ".Notes/></sources><syncml><Auth/><Conn/></syncml></spds></TaskCoach-\n"
            "0000011d209a4b6c3f9f7c32000a00b100240032\n"
            "><TaskCoach-0000011d209a4b6c3f9f7c32000a00b100240032><spds><sources><TaskCoach-0000011d209a4b6c3f9f7c32000a00b100240032.Tasks/><TaskCoach-0000011d209a4b6c3f9f7c32000a00b100240032.Notes/></sources><syncml><Auth/><Conn/></syncml></spds></TaskCoach-0000011d209a4b6c3f9f7c32000a00b100240032></syncml><guid>\n"
            "0000011d209a4b6c3f9f7c32000a00b100240032\n"
            "</guid></tasks>"
        )
        self.assertEqual(expectedGUID, actualGUID)


class XMLReaderVersion26Test(XMLReaderTestCase):
    tskversion = 26  # New in release 0.75.0

    # Release 0.75.0 introduces percentage complete for tasks

    def testPercentageComplete(self):
        tasks = self.writeAndReadTasks(
            '<tasks>\n<task subject="Task" status="0" percentageComplete="50"/>\n'
            "</tasks>\n"
        )
        self.assertEqual(50, tasks[0].percentageComplete())


class XMLReaderVersion27Test(XMLReaderTestCase):
    tskversion = 27  # New in release 0.76.0

    # Release 0.76.0 introduces exclusive subcategories

    def testExclusiveSubcategories(self):
        categories = self.writeAndReadCategories(
            "<categories>\n"
            '<category subject="Category" exclusiveSubcategories="True"'
            ' status="0"/>\n'
            "</categories>\n"
        )
        self.assertTrue(categories[0].hasExclusiveSubcategories())

    def testNoExclusiveSubcategoriesByDefault(self):
        categories = self.writeAndReadCategories(
            "<categories>\n"
            '<category subject="Category" status="0"/>\n'
            "</categories>\n"
        )
        self.assertFalse(categories[0].hasExclusiveSubcategories())


class XMLReaderVersion28Test(XMLReaderTestCase):
    tskversion = 28  # New in release 0.78.0

    # Release 0.78.0 introduces foreground colors and fonts that can be set per object.

    def testTaskForegroundColor(self):
        tasks = self.writeAndReadTasks(
            '<tasks>\n<task subject="Task" fgColor="(255,0,0)"/>\n'
            "</tasks>\n"
        )
        self.assertEqual(wx.RED, tasks[0].foregroundColor())

    def testTaskBackgroundColor(self):
        tasks = self.writeAndReadTasks(
            '<tasks>\n<task subject="Task" bgColor="(255,0,0)"/>\n'
            "</tasks>\n"
        )
        self.assertEqual(wx.RED, tasks[0].backgroundColor())

    def testCategoryForegroundColor(self):
        categories = self.writeAndReadCategories(
            '<categories>\n<category subject="Category" fgColor="(255,0,0)"/>\n'
            "</categories>\n"
        )
        self.assertEqual(wx.RED, categories[0].foregroundColor())

    def testCategoryBackgroundColor(self):
        categories = self.writeAndReadCategories(
            '<categories>\n<category subject="Category" bgColor="(255,0,0)"/>\n'
            "</categories>\n"
        )
        self.assertEqual(wx.RED, categories[0].backgroundColor())

    def testNoteForegroundColor(self):
        notes = self.writeAndReadNotes(
            '<notes>\n<note subject="Note" fgColor="(255,0,0)"/>\n'
            "</notes>\n"
        )
        self.assertEqual(wx.RED, notes[0].foregroundColor())

    def testNoteBackgroundColor(self):
        notes = self.writeAndReadNotes(
            '<notes>\n<note subject="Note" bgColor="(255,0,0)"/>\n'
            "</notes>\n"
        )
        self.assertEqual(wx.RED, notes[0].backgroundColor())

    def testTaskFont(self):
        tasks = self.writeAndReadTasks(
            '<tasks>\n<task subject="Task" font="%s"/>\n'
            "</tasks>\n" % wx.NORMAL_FONT.GetNativeFontInfoDesc()
        )
        self.assertEqual(wx.NORMAL_FONT, tasks[0].font())

    def testNoTaskFont(self):
        tasks = self.writeAndReadTasks(
            '<tasks>\n<task subject="Task"/>\n</tasks>\n'
        )
        self.assertEqual(None, tasks[0].font())

    def testCategoryFont(self):
        categories = self.writeAndReadCategories(
            '<categories>\n<category subject="Category" font="%s"/>\n'
            "</categories>\n" % wx.NORMAL_FONT.GetNativeFontInfoDesc()
        )
        self.assertEqual(wx.NORMAL_FONT, categories[0].font())

    def testNoteFont(self):
        notes = self.writeAndReadNotes(
            '<notes>\n<note subject="Note" font="%s"/>\n'
            "</notes>\n" % wx.NORMAL_FONT.GetNativeFontInfoDesc()
        )
        self.assertEqual(wx.NORMAL_FONT, notes[0].font())

    def testAttachmentFont(self):
        tasks = self.writeAndReadTasks(
            '<tasks>\n<task subject="Task">\n'
            '<attachment type="file" location="whatever" font="%s"/>\n'
            "</task>\n</tasks>\n" % wx.NORMAL_FONT.GetNativeFontInfoDesc()
        )
        self.assertEqual(wx.NORMAL_FONT, tasks[0].attachments()[0].font())


class XMLReaderVersion29Test(XMLReaderTestCase):
    tskversion = 29

    def testEffortNewId(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task id="foo">
                <effort id="foobar" start="2004-01-01 10:00:00.123000"
                        stop="2004-01-01 10:30:00.123000"
                        status="1"
                        description="Yo"/>
            </task>
        </tasks>""")
        self.assertEqual("foobar", tasks[0].efforts()[0].id())

    def testTaskIcon(self):
        tasks = self.writeAndReadTasks('<tasks><task icon="icon"/></tasks>')
        self.assertEqual("icon", tasks[0].icon())

    def testSelectedTaskIcon(self):
        tasks = self.writeAndReadTasks(
            '<tasks><task selectedIcon="icon"/></tasks>'
        )
        self.assertEqual("icon", tasks[0].selectedIcon())

    def testNoteIcon(self):
        notes = self.writeAndReadNotes('<tasks><note icon="icon"/></tasks>')
        self.assertEqual("icon", notes[0].icon())

    def testSelectedNoteIcon(self):
        notes = self.writeAndReadNotes(
            '<tasks><note selectedIcon="icon"/></tasks>'
        )
        self.assertEqual("icon", notes[0].selectedIcon())

    def testCategoryIcon(self):
        categories = self.writeAndReadCategories(
            '<tasks><category icon="icon"/></tasks>'
        )
        self.assertEqual("icon", categories[0].icon())

    def testSelectedCategoryIcon(self):
        categories = self.writeAndReadCategories(
            '<tasks><category selectedIcon="icon"/></tasks>'
        )
        self.assertEqual("icon", categories[0].selectedIcon())

    def testAttachmentIcon(self):
        tasks = self.writeAndReadTasks(
            '<tasks><task subject="Task">'
            '<attachment type="file" location="whatever" icon="icon"/>'
            "</task></tasks>"
        )
        self.assertEqual("icon", tasks[0].attachments()[0].icon())

    def testSelectedAttachmentIcon(self):
        tasks = self.writeAndReadTasks(
            '<tasks><task subject="Task">'
            '<attachment type="file" location="whatever" selectedIcon="icon"/>'
            "</task></tasks>"
        )
        self.assertEqual("icon", tasks[0].attachments()[0].selectedIcon())


class XMLReaderVersion30Test(XMLReaderTestCase):
    tskversion = 30  # New in release 1.1.0.

    def testStartDateTime(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task startdate="2005-04-17 10:05:11"/>
        </tasks>\n""")
        self.assertEqual(
            date.DateTime(2005, 4, 17, 10, 5, 11),
            tasks[0].plannedStartDateTime(),
        )

    def testStartDateTimeWithoutTime(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task startdate="2005-04-17"/>
        </tasks>\n""")
        self.assertEqual(
            date.DateTime(2005, 4, 17), tasks[0].plannedStartDateTime()
        )

    def testNoStartDateTime(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task />
        </tasks>\n""")
        self.assertEqual(date.DateTime(), tasks[0].plannedStartDateTime())

    def testStartDateTimeWithMicroseconds(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task startdate="2005-01-01 22:01:30.456"/>
        </tasks>\n""")
        self.assertEqual(
            date.DateTime(2005, 1, 1, 22, 1, 30, 456),
            tasks[0].plannedStartDateTime(),
        )

    def testDueDateTime(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task duedate="2005-04-17 13:05:59"/>
        </tasks>\n""")
        self.assertEqual(
            date.DateTime(2005, 4, 17, 13, 5, 59), tasks[0].dueDateTime()
        )

    def testDueDateTimeWithoutTime(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task duedate="2005-04-17"/>
        </tasks>\n""")
        self.assertEqual(
            date.DateTime(2005, 4, 17, 23, 59, 59, 999999),
            tasks[0].dueDateTime(),
        )

    def testDueDateTimeWithoutTimeWhenEndHourIs24(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task duedate="2005-04-17"/>
        </tasks>\n""")
        self.assertEqual(
            date.DateTime(2005, 4, 17, 23, 59, 59, 999999),
            tasks[0].dueDateTime(),
        )

    def testNoDueDateTime(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task />
        </tasks>\n""")
        self.assertEqual(date.DateTime(), tasks[0].dueDateTime())

    def testDueDateTimeWithMicroseconds(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task duedate="2005-01-01 22:01:30.456000"/>
        </tasks>\n""")
        self.assertEqual(
            date.DateTime(2005, 1, 1, 22, 1, 30, 456000),
            tasks[0].dueDateTime(),
        )

    def testCompletionDateTime(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task completiondate="2005-01-01 22:01:30"/>
        </tasks>\n""")
        self.assertEqual(
            date.DateTime(2005, 1, 1, 22, 1, 30), tasks[0].completionDateTime()
        )
        self.assertTrue(tasks[0].completed())

    def testCompletionDateTimeWithMicroseconds(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task completiondate="2005-01-01 22:01:30.456000"/>
        </tasks>\n""")
        self.assertEqual(
            date.DateTime(2005, 1, 1, 22, 1, 30, 456000),
            tasks[0].completionDateTime(),
        )
        self.assertTrue(tasks[0].completed())

    def testNoCompletionDateTime(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task />
        </tasks>\n""")
        self.assertEqual(date.DateTime(), tasks[0].completionDateTime())

    def testCompletionDateTimeWithoutTime(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task completiondate="2005-01-01"/>
        </tasks>\n""")
        self.assertEqual(
            date.DateTime(2005, 1, 1, 23, 59, 59, 999999),
            tasks[0].completionDateTime(),
        )
        self.assertTrue(tasks[0].completed())

    def testEmptyFontDescription(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task font=""/>
        </tasks>\n""")
        self.assertEqual(None, tasks[0].font())

    def testHelveticaMacFont(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task font="0;11;70;90;90;0;Helvetica Neue Light;0"/>
        </tasks>\n""")
        size = tasks[0].font().GetPointSize()
        if operating_system.isMac():  # pragma: no cover
            self.assertEqual(11, size)
        else:  # pragma: no cover
            self.assertTrue(size > 0)

    def testSans9LinuxFont(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task font="Sans 9"/>
        </tasks>\n""")
        if operating_system.isMac():  # pragma: no cover
            self.assertEqual(None, tasks[0].font())
        else:  # pragma: no cover
            expectedFontSize = 9 if operating_system.isGTK() else 8
            self.assertEqual(expectedFontSize, tasks[0].font().GetPointSize())


class XMLReaderVersion31Test(XMLReaderTestCase):
    tskversion = 31  # New in release 1.2.0.

    def writeAndReadTasks(self, *args, **kwargs):
        tasks = super(XMLReaderVersion31Test, self).writeAndReadTasks(
            *args, **kwargs
        )
        tasksById = dict()

        def collectIds(tasks):
            for eachTask in tasks:
                tasksById[eachTask.id()] = eachTask
                collectIds(eachTask.children())

        collectIds(tasks)
        return tasksById

    def assertDepends(self, prerequisite, dependency):
        self.assertTrue(prerequisite in dependency.prerequisites())
        self.assertTrue(dependency in prerequisite.dependencies())

    def testOnePrerequisite(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task id="1"/>
            <task id="2" prerequisites="1"/>
        </tasks>\n""")
        self.assertDepends(tasks["1"], tasks["2"])

    def testTwoPrerequisites(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task id="1"/>
            <task id="2" prerequisites="1 3"/>
            <task id="3"/>
        </tasks>\n""")
        self.assertDepends(tasks["1"], tasks["2"])
        self.assertDepends(tasks["3"], tasks["2"])

    def testChainOfPrerequisites(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task id="1"/>
            <task id="2" prerequisites="1"/>
            <task id="3" prerequisites="2"/>
        </tasks>\n""")
        self.assertDepends(tasks["1"], tasks["2"])
        self.assertDepends(tasks["2"], tasks["3"])

    def testSubTaskPrerequisite(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task id="1">
                <task id="1.1"/>
            </task>
            <task id="2" prerequisites="1.1"/>
        </tasks>\n""")
        self.assertDepends(tasks["1.1"], tasks["2"])

    def testInterSubTaskPrerequisite(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task id="1">
                <task id="1.1"/>
                <task id="1.2" prerequisites="1.1"/>
            </task>
        </tasks>\n""")
        self.assertDepends(tasks["1.1"], tasks["1.2"])

    def testMutualPrerequisites(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task id="1" prerequisites="2"/>
            <task id="2" prerequisites="1"/>
        </tasks>\n""")
        self.assertDepends(tasks["1"], tasks["2"])
        self.assertDepends(tasks["2"], tasks["1"])

    def testMutualPrerequisiteWithChild(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task id="1" prerequisites="1.1">
                <task id="1.1" prerequisites="1"/>
            </task>
        </tasks>\n""")
        self.assertDepends(tasks["1"], tasks["1.1"])
        self.assertDepends(tasks["1.1"], tasks["1"])

    def testSelfPrerequisite(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task id="1" prerequisites="1"/>
        </tasks>\n""")
        self.assertDepends(tasks["1"], tasks["1"])

    def asserTrue(self, param):
        pass


class XMLReaderVersion33Test(XMLReaderTestCase):
    tskversion = 33  # New in release 1.2.24.

    def testReminderBeforeSnooze(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task reminder="2004-01-01 10:00:00"
                  reminderBeforeSnooze="2004-01-01 9:00:00"/>
        </tasks>\n""")
        self.assertEqual(
            date.DateTime(2004, 1, 1, 9, 0, 0),
            tasks[0].reminder(includeSnooze=False),
        )
        self.assertEqual(
            date.DateTime(2004, 1, 1, 10, 0, 0), tasks[0].reminder()
        )

    def testReminder(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task reminder="2004-01-01 10:00:00"/>
        </tasks>\n""")
        self.assertEqual(
            date.DateTime(2004, 1, 1, 10, 0, 0),
            tasks[0].reminder(includeSnooze=False),
        )
        self.assertEqual(
            date.DateTime(2004, 1, 1, 10, 0, 0), tasks[0].reminder()
        )

    def testRecurrenceNotBasedOnCompletion(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task><recurrence unit="daily"/></task>
        </tasks>""")
        self.assertFalse(tasks[0].recurrence().recurBasedOnCompletion)

    def testRecurrenceBasedOnCompletion(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task>
                <recurrence unit="daily" recurBasedOnCompletion="True"/>
            </task>
        </tasks>""")
        self.assertTrue(tasks[0].recurrence().recurBasedOnCompletion)


class XMLReaderVersion34Test(XMLReaderTestCase):
    tskversion = 34  # New in release 1.3.5.

    def testPlannedStartDateTime(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task plannedstartdate="2005-04-17 10:05:11"/>
        </tasks>\n""")
        self.assertEqual(
            date.DateTime(2005, 4, 17, 10, 5, 11),
            tasks[0].plannedStartDateTime(),
        )

    def testPlannedStartDateTimeWithoutTime(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task plannedstartdate="2005-04-17"/>
        </tasks>\n""")
        self.assertEqual(
            date.DateTime(2005, 4, 17), tasks[0].plannedStartDateTime()
        )

    def testNoPlannedStartDateTime(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task />
        </tasks>\n""")
        self.assertEqual(date.DateTime(), tasks[0].plannedStartDateTime())

    def testPlannedStartDateTimeWithMicroseconds(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task plannedstartdate="2005-01-01 22:01:30.456"/>
        </tasks>\n""")
        self.assertEqual(
            date.DateTime(2005, 1, 1, 22, 1, 30, 456),
            tasks[0].plannedStartDateTime(),
        )

    def testActualStartDateTime(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task actualstartdate="2005-04-17 10:05:11"/>
        </tasks>\n""")
        self.assertEqual(
            date.DateTime(2005, 4, 17, 10, 5, 11),
            tasks[0].actualStartDateTime(),
        )

    def testActualStartDateTimeWithoutTime(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task actualstartdate="2005-04-17"/>
        </tasks>\n""")
        self.assertEqual(
            date.DateTime(2005, 4, 17), tasks[0].actualStartDateTime()
        )

    def testNoActualStartDateTime(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task />
        </tasks>\n""")
        self.assertEqual(date.DateTime(), tasks[0].actualStartDateTime())

    def testActualStartDateTimeWithMicroseconds(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task actualstartdate="2005-01-01 22:01:30.456"/>
        </tasks>\n""")
        self.assertEqual(
            date.DateTime(2005, 1, 1, 22, 1, 30, 456),
            tasks[0].actualStartDateTime(),
        )

    def testTaskWithNoteWithCategory(self):
        tasks, categories = self.writeAndReadTasksAndCategories("""
        <tasks>
            <task>
                <note subject="note" id="note1"/>
            </task>
            <category id="cat1" categorizables="note1"/>
        </tasks>\n""")
        self.assertEqual(
            list(tasks[0].notes())[0], list(categories[0].categorizables())[0]
        )


class XMLReaderVersion35Test(XMLReaderTestCase):
    tskversion = 35  # New in release 1.3.19.

    def testRecurrenceStopDateTime(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task>
                <recurrence stop_datetime="2000-01-10 13:13:13"/>
            </task>
        </tasks>""")
        self.assertEqual(
            date.DateTime(2000, 1, 10, 13, 13, 13),
            tasks[0].recurrence().stop_datetime,
        )

    def testCreationDateTimeIsSetToMinDateTime(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task/>
        </tasks>""")
        self.assertEqual(date.DateTime.min, tasks[0].creationDateTime())


class XMLReaderVersion36Test(XMLReaderTestCase):
    tskversion = 36  # New in release 1.3.21

    def testCreationDateTime(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task creationDateTime="2012-12-12 12:00:00.12345"/>
        </tasks>""")
        self.assertEqual(
            date.DateTime(2012, 12, 12, 12, 0, 0, 12345),
            tasks[0].creationDateTime(),
        )


class XMLReaderVersion37Test(XMLReaderTestCase):
    tskversion = 37  # New in release 1.3.23

    def testModificationDateTime(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task modificationDateTime="2012-12-12 12:00:00.12345"/>
        </tasks>""")
        self.assertEqual(
            date.DateTime(2012, 12, 12, 12, 0, 0, 12345),
            tasks[0].modificationDateTime(),
        )

    def testModificationDateTimeWithOtherAttributes(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
            <task modificationDateTime="2012-12-12 12:00:00.12345"/>
        </tasks>""")
        self.assertEqual(
            date.DateTime(2012, 12, 12, 12, 0, 0, 12345),
            tasks[0].modificationDateTime(),
        )

    def testAdjustDueDateTime(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
          <task duedate="2012-12-12 23:59:00:000000" />
        </tasks>""")
        self.assertEqual(
            date.DateTime(2012, 12, 12, 23, 59, 59, 999999),
            tasks[0].dueDateTime(),
        )

    def test_dontAdjustPlannedStartDateTime(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
          <task plannedstartdate="2012-12-12 23:59:00:000000" />
        </tasks>""")
        self.assertEqual(
            date.DateTime(2012, 12, 12, 23, 59, 0, 0),
            tasks[0].plannedStartDateTime(),
        )

    def test_dontAdjustActualStartDateTime(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
          <task actualstartdate="2012-12-12 23:59:00:000000" />
        </tasks>""")
        self.assertEqual(
            date.DateTime(2012, 12, 12, 23, 59, 0, 0),
            tasks[0].actualStartDateTime(),
        )

    def test_dontAdjustCompletionDateTime(self):
        tasks = self.writeAndReadTasks("""
        <tasks>
          <task completiondate="2012-12-12 23:59:00:000000" />
        </tasks>""")
        self.assertEqual(
            date.DateTime(2012, 12, 12, 23, 59, 0, 0),
            tasks[0].completionDateTime(),
        )

    def testTaskNoteCategory(self):
        categories = self.writeAndReadCategories("""
        <tasks>
          <task>
            <note id="noteid" />
          </task>
          <category categorizables="noteid" />
        </tasks>""")
        self.assertTrue(
            "noteid" in [obj.id() for obj in categories[0].categorizables()]
        )

    def testSubtaskNoteCategory(self):
        categories = self.writeAndReadCategories("""
        <tasks>
          <task>
            <task>
              <note id="noteid" />
            </task>
          </task>
          <category categorizables="noteid" />
        </tasks>""")
        self.assertTrue(
            "noteid" in [obj.id() for obj in categories[0].categorizables()]
        )

    def testCategoryNoteCategory(self):
        categories = self.writeAndReadCategories("""
        <tasks>
          <category categorizables="noteid">
            <note id="noteid" />
          </category>
        </tasks>""")
        self.assertTrue(
            "noteid" in [obj.id() for obj in categories[0].categorizables()]
        )

    def testSubcategoryNoteCategory(self):
        categories = self.writeAndReadCategories("""
        <tasks>
          <category categorizables="noteid">
            <category>
              <note id="noteid" />
            </category>

          </category>
        </tasks>""")
        self.assertTrue(
            "noteid" in [obj.id() for obj in categories[0].categorizables()]
        )

    def testTaskAttachmentNoteCategory(self):
        categories = self.writeAndReadCategories("""
        <tasks>
          <task>
            <attachment location="test" type="file">
              <note id="noteid" />
            </attachment>
          </task>
          <category categorizables="noteid" />
        </tasks>""")
        self.assertTrue(
            "noteid" in [obj.id() for obj in categories[0].categorizables()]
        )

    def testSubtaskAttachmentNoteCategory(self):
        categories = self.writeAndReadCategories("""
        <tasks>
          <task subject="Task">
            <task subject="Subtask">
              <attachment location="test" type="file" subject="Attachment">
                <note id="noteid" subject="Note" />
              </attachment>
            </task>
          </task>
          <category categorizables="noteid" subject="Category" />
        </tasks>""")
        self.assertTrue(
            "noteid" in [obj.id() for obj in categories[0].categorizables()]
        )


class XMLReaderVersion38Test(XMLReaderTestCase):
    tskversion = 38  # New in release 2.0 in python 3

    def testMinimalCategoryResolution(self):
        tasks, categories = self.writeAndReadTasksAndCategories(
            "<tasks>"
            '    <task id="1">'
            "        <category>test</category>"
            "    </task>"
            "    <categories>"
            '        <category id="test"/>'
            "    </categories>"
            "</tasks>"
        )
        testCategory = categories[0]
        # print(f"Catégorie \'test\' contient : {[obj.id() for obj in testCategory.categorizables()]}")
        self.assertEqual("1", list(testCategory.categorizables())[0].id())
