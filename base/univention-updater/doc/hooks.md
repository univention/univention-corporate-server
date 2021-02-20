The Online Update Module supports the hooks which are called
once at module startup.
These hooks may reside within a single Python file that has to be placed in the
directory `/usr/share/univention-updater/hooks/´.
The content of an example hookfile is placed below.

Hook `updater_show_message`
===========================
This hook is called to allow 3rd party software to display messages within the
Online Update Module. The returned message will be displayed in a separate
TitlePane for each hook.

This hook has to return a Python dictionary:

| Key      |  Type     |  Description                                         | Required   |
| -------- | --------- | ---------------------------------------------------- | ---------- |
| valid    |  Boolean  |  Indicates if this hooks wants to display a message  | always     |
| title    |  String   |  title of displayed TitlePane                        | if `valid` |
| message  |  String   |  content of TitlePane                                | if `valid` |


Hook `updater_prohibit_update`
==============================
This hook is called to allow 3rd party software to block further updates. Please use
this feature only if the update would fail or break the system otherwise.
Each hook has to return a Boolean. If at least one hook returns the value True, the
update related TitlePanes will not be displayed to the user.


Example myhook.py
=================

```python
def my_msg(*args, **kwargs):
    # type: (*Any, **Any) -> TypedDict["Message", {"valid": bool, "title": str, "message": str}, total=False]
    return {
        'valid': True,
        'title': 'The Title Of The TitlePane',
        'message': '<p>The content of the <b>TitlePane</b></p>'
    }

def my_block(*args, **kwargs):
    # type: (*Any, **Any) -> bool
    return True

def register_hooks():
    # type: () -> List[Tuple[str. Callable[..., object]]]
    return [
        ('updater_show_message', my_msg),
        ('updater_prohibit_update', my_block),
    ]
```
