from imaplib import IMAP4
from ntlm import IMAPNtlmAuthHandler
import os
import sys

def main():
    assert len( sys.argv ) == 3, "Usage %s <password> <host>" % sys.argv[0]
    user = '%s\%s' % ( os.environ["USERDOMAIN"], os.environ["USERNAME"] )
    password = sys.argv[1]
    host = sys.argv[2]

    imap = IMAP4(host)
    imap.authenticate("NTLM", IMapNtlmAuthHandler(user, password))
    
    M.select()
    typ, data = M.search(None, 'ALL')
    for num in data[0].split():
        typ, data = M.fetch(num, '(RFC822)')
        print 'Message %s\n%s\n' % (num, data[0][1])
    M.close()
    M.logout()
