# ----------------------------------------------------------------------------
# "THE BEER-WARE LICENSE":
# <chad@zetaweb.com> wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return. --Chad Whitacre
# ----------------------------------------------------------------------------

import os, re, imaplib, smtplib, email
from os.path import join
from ConfigParser import SafeConfigParser as ConfigParser

class Kraken:
    """

    This guy polls an IMAP account. If a new message is from a list member, then
    it forwards the message along to the rest of the list. Otherwise it moves
    the message to the trash. Usage:

    >>> FROM = 'From: Chad Whitacre <douglas.wicker@pncyeah.com>'
    >>> pattern = r'From:.* <?(.*@.*\..*)>?$'
    >>> from_addr = re.search(pattern, FROM).group(1)
    >>> print from_addr

    #>>> from Kraken import Kraken
    #>>> k = Kraken()
    #>>> k.release()

    """

    def __init__(self, root='.'):
        """ read in config info """

        conf_path = join(root,'conf/kraken.conf')
        send_path = join(root,'conf/send_to.conf')
        from_path = join(root,'conf/also_accept_from.conf')

        cp = ConfigParser()
        cp.read(conf_path)
        self.imap = dict(cp.items('imap'))
        self.smtp = dict(cp.items('smtp'))
        self.list_addr = cp.get('default', 'list_addr')

        self.send_to = self.addrs(send_path)
        self.accept_from = self.send_to + \
                           self.addrs(from_path)


    def addrs(self, fn):
        """ given a filename, return a list of email addresses """
        raw = file(fn).read()
        lines = [l.strip() for l in raw.split(os.linesep)]
        return [l for l in lines
                  if not l.startswith('#') and
                     not l == '']
        # maybe eventually validate email addresses


    def release(self):
        """ get all mail from our inbox and process """

        imap = self.imap
        smtp = self.smtp

        # open the IMAP connection and get everything in the INBOX

        if imap['secure'] == 'True':
            raise 'NotImplemented', 'secure IMAP is not implemented yet'
        else:
            M = imaplib.IMAP4(imap['server'], int(imap['port']))
            M.login(imap['username'], imap['password'])
            M.select()
            typ, raw = M.search(None, 'ALL')
            msg_nums = raw[0].split()


        if len(msg_nums) == 0:

            # print '/me twiddles its thumbs'
            # only do something -- and only tell us -- if you actually
            # have something to do

            return

        else:

            i_good = i_bad = 0

            for num in msg_nums:

                # get the From header

                typ, raw = M.fetch(num, '(BODY[HEADER.FIELDS (FROM)])')
                FROM = raw[0][1]
                pattern = r'From:.* <?(.*@.*\.[A-Za-z]*)>?'
                from_addr = re.search(pattern, FROM).group(1)


                # and compare it to our membership lists

                if from_addr in self.accept_from:

                    # get the raw email
                    typ, raw = M.fetch(num, '(RFC822)')
                    raw = raw[0][1]
                    msg = email.message_from_string(raw)

                    # tweak the headers
                    try:
                        msg.replace_header('Reply-To', self.list_addr)
                    except KeyError:
                        msg.__setitem__('Reply-To', self.list_addr)
                    msg.add_header('X-Released-By','THE KRAKEN!!!!!!!!1')

                    # and pass it on!
                    if smtp['secure'] == 'True':
                       raise 'NotImplemented', 'secure SMTP is not implemented yet'
                    else:
                        server = smtplib.SMTP(smtp['server'],smtp['port'])
                        server.login(smtp['username'],smtp['password'])
                        server.sendmail(self.list_addr,self.send_to,msg.__str__())
                        server.quit()

                    # and move to archive
                    M.copy(num, 'Archive')
                    M.store(num, 'FLAGS.SILENT', '(\Deleted)')

                    i_good += 1

                else:
                    # move it to trash!
                    M.copy(num, 'Trash')
                    M.store(num, 'FLAGS.SILENT', '(\Deleted)')

                    i_bad += 1

            M.close()
            M.logout()

            print 'approved %s; rejected %s' % (i_good, i_bad)


def _test():
    import doctest, Kraken
    return doctest.testmod(Kraken)

if __name__ == "__main__":
    _test()
