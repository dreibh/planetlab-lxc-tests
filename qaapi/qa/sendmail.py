import os
import sys
import pprint
from types import StringTypes
from email.MIMEText import MIMEText
from email.Header import Header
from smtplib import SMTP


def sendmail(To, Subject, Body, From = None, Cc = None, Bcc = None):
    """
    Uses sendmail (must be installed and running locally) to send a
    message to the specified recipients. If the API is running under
    mod_python, the apache user must be listed in e.g.,
    /etc/mail/trusted-users.

    To, Cc, and Bcc may be addresses or lists of addresses. Each
    address may be either a plain text address or a tuple of (name,
    address).
    """

    # Fix up defaults
    if not isinstance(To, list):
        To = [To]
    if Cc is not None and not isinstance(Cc, list):
        Cc = [Cc]
    if Bcc is not None and not isinstance(Bcc, list):
        Bcc = [Bcc]
    if From is None:
        From = ("Quality Assurance <qa@planet-lab.org>")

    # Create a MIME-encoded UTF-8 message
    msg = MIMEText(Body.encode("utf-8"), _charset = "utf-8")

    # Unicode subject headers are automatically encoded correctly
    msg['Subject'] = Subject

    def encode_addresses(addresses, header_name = None):
        """
        Unicode address headers are automatically encoded by
        email.Header, but not correctly. The correct way is to put the
        textual name inside quotes and the address inside brackets:

        To: "=?utf-8?b?encoded" <recipient@domain>

        Each address in addrs may be a tuple of (name, address) or
        just an address. Returns a tuple of (header, addrlist)
        representing the encoded header text and the list of plain
        text addresses.
        """

        header = []
        addrs = []

        for addr in addresses:
            if isinstance(addr, tuple):
                (name, addr) = addr
                try:
                    name = name.encode('ascii')
                    header.append('%s <%s>' % (name, addr))
                except:
                    h = Header(name, charset = "utf-8", header_name = header_name)
                    header.append('"%s" <%s>' % (h.encode(), addr))
            else:
                header.append(addr)
            addrs.append(addr)

        return (", ".join(header), addrs)

    (msg['From'], from_addrs) = encode_addresses([From], 'From')
    (msg['To'], to_addrs) = encode_addresses(To, 'To')

    if Cc is not None:
        (msg['Cc'], cc_addrs) = encode_addresses(Cc, 'Cc')
        to_addrs += cc_addrs

    if Bcc is not None:
        (unused, bcc_addrs) = encode_addresses(Bcc, 'Bcc')
        to_addrs += bcc_addrs

    # Needed to pass some spam filters
    msg['Reply-To'] = msg['From']
    msg['X-Mailer'] = "Python/" + sys.version.split(" ")[0]

    s = SMTP()
    s.connect()
    rejected = s.sendmail(from_addrs[0], to_addrs, msg.as_string(), rcpt_options = ["NOTIFY=NEVER"])
    s.close()

    if rejected:
        raise Exception, "Error sending message to " + ", ".join(rejected.keys())
