High-Level-Overview
===================

[UCSRepoPool{,5,NoArch}](../modules/univention/updater/tools.py):
	Structure on a repository server, relative to some UCS*Server

[UCS{Http,Local}Server](../modules/univention/updater/tools.py):
	Access to a repository server, providing the root for UCSRepo*

[UniventionUpdater](../modules/univention/updater/tools.py):
	High level functions to handle releases, security updates and components.
	Using UCR variables repository/online**

[LocalUpdater](../modules/univention/updater/tools.py):
	Specialized version of UniventionUpdater using local file access for the local repository.

[UniventionMiror](../modules/univention/updater/mirror.py):
	High level functions to handle the mirroring of remote repositories to the local repository, normally /var/lib/univention-repository/
	Using UCR variables repository/mirror**

Tools
=====

Upgrade
-------

[univention-upgrade](../modules/univention/updater/scripts/upgrade.py) is the high-level tool to perform upgrades.
1.  Check for pending package upgrades
2.  Check for pending App updates
3.  Check for new UCS release updates: this is performed by [univention-updater](../modules/univention/updater/scripts/updater.py)

Updater
-------

[univention-updater](../modules/univention/updater/scripts/updater.py) is the low-level tool to perform release upgrades.

[Sequence of events](https://docs.software-univention.de/developer-reference-5.0.html#updater:release-update)


Actualize
---------

[univention-actualize](../modules/univention/updater/scripts/actualize.py) does package maintenance from policy,
* install required packages
* remove prevented packages
* perform pending package upgrades
