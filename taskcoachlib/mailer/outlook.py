
import os, tempfile

if os.name == 'nt':
    from win32com.client import GetActiveObject

    def getCurrentSelection():
        obj = GetActiveObject('Outlook.Application')
        exp = obj.ActiveExplorer()
        sel = exp.Selection

        ret = []
        for n in xrange(1, sel.Count + 1):
            filename = tempfile.mktemp('.eml')
            try:
                sel.Item(n).SaveAs(filename, 0)
                # Add Outlook internal ID as custom header... It seems
                # that some versions of Outlook don't put a blank line
                # between subject and headers.

                name = tempfile.mktemp('.eml')
                src = file(filename, 'rb')
                linenb = 0

                try:
                    dst = file(name, 'wb')
                    try:
                        s = 0
                        for line in src:
                            linenb += 1
                            if s == 0:
                                if line.strip() == '' or linenb == 5:
                                    dst.write('X-Outlook-ID: %s\r\n' % str(sel.Item(n).EntryID))
                                    s = 1
                                if linenb == 5 and line.strip() != '':
                                    dst.write('\r\n')
                            dst.write(line)
                    finally:
                        dst.close()
                finally:
                    src.close()
                ret.append(name)
            finally:
                os.remove(filename)

        return ret
