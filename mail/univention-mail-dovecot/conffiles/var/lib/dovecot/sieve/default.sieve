@%@UCRWARNING=# @%@

@!@
import time
import math
import sys

# get spam required hits in "*"
try:
	flo = float(configRegistry.get("mail/antispam/requiredhits", "5.0"))
	spamHits = int(math.ceil(flo))
except:
	spamHits = 5
spamHitsValue = spamHits*"*"

folder = configRegistry.get('mail/dovecot/folder/spam')
if not folder or folder.lower() == "none":
	print "# Please set 'mail/dovecot/folder/spam'."
else:
	print  """# Univention Sieve Script - generated on %(date)s
require ["fileinto", "mailbox"];

# Spamfilter
if header :contains "X-Spam-Level" "%(hits)s"  {
	fileinto :create "%(folder)s";
	stop;
}""" % {"date": time.asctime(time.localtime()), "hits": spamHitsValue, "folder": folder}
@!@
