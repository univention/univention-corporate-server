.. _mail-spam:

Spam detection and filtering
============================

Undesirable and unsolicited e-mails are designated as Spam. The software
SpamAssassin and Postgrey are integrated in UCS for the automatic identification
of these e-mails. SpamAssassin attempts to identify whether an e-mail is
desirable or not based on heuristics concerning its origin, form and content.
Postgrey is a policy server for Postfix, which implements gray listing. Grey
listing is a Spam detection method which denies the first delivery attempt of
external mail servers. Mail servers of Spam senders most often do not perform a
second delivery attempt, while legitimate servers do so. Integration occurs via
the packages :program:`univention-spamassassin` and
:program:`univention-postgrey`, which are automatically set up during the
installation of the mail server package.

SpamAssassin operates a point system, which uses an increasing number of points
to express a high probability of the e-mail being Spam. Points are awarded
according to different criteria, for example, keywords within the e-mail or
incorrect encodings. In the standard configuration only mails with a size of up
to 300 kilobytes are scanned, this can be adjusted using the |UCSUCRV|
:envvar:`mail/antispam/bodysizelimit`.

E-mails which are classified as Spam - because they exceed a certain number of
points - are not delivered to the recipient's inbox by Dovecot, but rather in
the *Spam* folder below it. The name of the folder for Spam can be configured
with the |UCSUCRV| :envvar:`mail/dovecot/folder/Spam`. The filtering is
performed by a Sieve script, which is automatically generated when the user is
created.

The threshold in these scripts as of which e-mails are declared to be Spam can
be configured with the |UCSUCRV| :envvar:`mail/antispam/requiredhits`. The
presetting (``5``) generally does not need to be adjusted. However, depending
on experience in the local environment, this value can also be set lower. This
will, however, result in more e-mails being incorrectly designated as Spam.
Changes to the threshold do not apply to existing users.

There is also the possibility of evaluating e-mails with a Bayes classifier.
This compares an incoming e-mail with statistical data already gathered from
processed e-mails and uses this to adapt it's evaluation to the user's e-mail.
The Bayes classification is controlled by the user himself, whereby e-mails not
identified as Spam by the system can be placed in the *Spam* subfolder by the
user and a selection of legitimate e-mails copied into the *Ham*
(:envvar:`mail/dovecot/folder/ham`) subfolder. This folder is evaluated daily
and data which have not yet been collected or were previously classified
incorrectly are collected in a shared database. This evaluation is activated by
default and can be configured with the |UCSUCRV|
:envvar:`mail/antispam/learndaily`.

The Spam filtering can be deactivated by setting the |UCSUCRV|
:envvar:`mail/antivir/spam` to ``no``. When modifying Univention Configuration
Registry variables concerning Spam detection, the AMaViS service and Postfix
must be restarted subsequently.
