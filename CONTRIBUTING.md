# Contributing to Univention

:+1: :tada: Hello, we are happy that you want to contribute to Univention Corporate Server (UCS)! :tada: :+1:

Before you start, please read the following guidelines about contributing to the packages of UCS.

## Pull Requests

We appreciate every pull request which enhances the software or the documentation.

There are some requirements for submitting a Pull Request:

* You need to sign the [Contributor License Agreements](https://www.univention.com/about-us/open-source/contributor-agreement/). This can be done either by sending us a facsimile or digitally by filling out the form which is send to you after submitting the Pull Request.

* Please create an issue in the [bugzilla bug tracker](https://forge.univention.org/bugzilla/enter_bug.cgi). Changes in the documentation don't necessarily need an issue.

* Either the bug report or the pull request have to describe the problem and changes as exact as possible.

* All commit messages should contain the bug number in the format `Bug #12345`.

* The changes should be done in the current default branch, we are releasing changes only for [recent maintained UCS versions](https://wiki.univention.de/index.php?title=Maintenance_Cycle_for_UCS).

* Don't provide security fixes for issues which need to remain secret. Instead a patch can be submitted in [bugzilla bug tracker](https://forge.univention.org/bugzilla/enter_bug.cgi) which has the flag `univentionstaff` enabled.

## Code of Conduct

Please accept, that we can't approve every pull request immediately. We have to do certain things before a patch can go into Univention products:
* **Check for side effects**: Changes might introduce regressions or break behavior for other existing customers.
* **Adjust the documentation**
* **Consider security or usability aspects**
* **Prioritize against other tasks**: We are working on many topics, sometimes other things are more urgent.
* **Release management**: We need to decide which UCS release fits best.

You have influence on the time we take:

* **Be open and friendly**
* **Be patient**
* **Be agreeable**: Sometimes, we have another opinion.
* **Use English language**: Our preferred language is English. This makes it easier for all contributors to understand each other.
* **Provide relevant details**: Describe your environment and the problem, how it can be reproduced and how it was solved.
* **Think about other users**: Is the feature helpful for many users? Or is the change customer specific. Might there be a better solution which uses or provides an API?
* **Stick to the Style guide**

## Styleguide

For python code we are aligning on [PEP8](https://www.python.org/dev/peps/pep-0008/) with the following exceptions:

* Indentation must use tabulators instead of spaces.
* The maximum line length is not specified, but we suggest to keep it below 120.
* Code Cleanups should be within own commits so that the fix for the real problem is easy distinguishable.

We don't have style conventions for other programming languages, but we advise to keep it simple, clean and readable.
