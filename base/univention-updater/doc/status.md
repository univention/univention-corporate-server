univention-updater.status
=========================

The file `/var/lib/univention-updater/univention-updater.status` contains the current status of the update process.
Each line of the file consists of a key-value pair which may have the following values:

* `current_version` ==> `UCS_Version` ==> `2.3-1`
* `next_version` ==> `UCS_Version` ==> `2.3-2`
* `target_version` ==> `UCS_Version` ==> `2.4-0`
* `type` ==> `(LOCAL|NET)`
* `status` ==> `(RUNNING|FAILED|DONE)`
* `phase` ==> `(PREPARATION|PREUP|UPDATE|POSTUP)` ==> only valid if `status=RUNNING`
* `errorsource` ==> `(SETTINGS|PREPARATION|PREUP|UPDATE|POSTUP)`

Example:

    current_version=4.4-3
    next_version=4.4-4
    target_version=4.4-7
    type=LOCAL
    status=RUNNING
    phase=UPDATE
