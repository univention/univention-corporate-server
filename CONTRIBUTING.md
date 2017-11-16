# Contributing to Univention

:+1: :tada: Hello, we are happy that you want to contribute to our packages! :tada: :+1:

Before you start please read our following guidelines about contributing to all packages of Univention.

## Pull Requests

We appreciate every pull request which enhances our software or documentation.

There are some requirements for submitting a Pull Request:

* You need to sign our [Contributor License Agreements](https://www.univention.com/about-us/open-source/contributor-agreement/). This can be done either by sending us a FAX or digitally by filling out the form which is send to you after submitting the Pull Request.

* Please create a issue in our [bugzilla bug tracker](https://forge.univention.org/bugzilla/enter_bug.cgi). Changes in the documentation don't neccessarily need an issue.

* Either the bug report or the pull request have to describe the problem and changes as exact as possible.

* All commit messages should contain the bug number in the format `Bug #12345`.

* The changes should be done in our current default branch, we are releasing changes only for [recent maintained UCS versions](http://wiki.univention.de/index.php?title=Maintenance_Cycle_for_UCS).

* Don't provide security fixes for issues which need to remain secret. Instead a patch can be submitted in our [bugzilla](https://forge.univention.org/bugzilla/enter_bug.cgi) which has the flag `univentionstaff` enabled.

## Code of Conduct

Please accept, that we can't aproove every pull request immediately. We have to do certain things before a patch can go into our products:
* **Check for side effects** Changes might introduce regressions or break behavior for other existing customers
* **Adjust our documentation**
* **Consider security or usability aspects**
* **Priorize against other tasks** We are working on many topics, sometimes other things are more urgent
* **Release management** We need to decide which UCS release fits best.

You have influence on the time we take:

* **Be open and friendly**
* **Be patient**
* **Be agreeable** Sometimes we have another opinion.
* **Use English language**
Our preferred language is English. This makes it easier for all contributors to understand each other.
* **Provide relevant details**
Describe your environment and the problem, how it can be reproduced and how it was solved.
* **Think about other users** Is the feature helpful for many users? Or is the change customer specific. Might there be a better solution which uses or provide an API?
* **Stick to our Style guide**

## Styleguide

For python code we are aligning on [PEP8](https://www.python.org/dev/peps/pep-0008/) with the following exceptions:

* Indentation must use tabulators instead of spaces.

* The maximum line length is not specified, but we suggest to keep it below 120.

* Code Cleanups should be within own commits so that the fix for the real problem is easy distinguishable.

We don't have style conventions for other programming languages, but we advise to keep it simple, clean and readable.
