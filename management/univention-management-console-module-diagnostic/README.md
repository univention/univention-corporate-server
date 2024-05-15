UMC diagnostics module
======================

Put new Python module into directory [plugins/](umc/python/diagnostic/plugins/).

Template
--------

```python
#!/usr/bin/python3

from typing import Any, Callable, Dict, List, Optional

from univention.lib.i18n import Translation

from univention.management.console.modules.diagnostic import MODULE, Critical, Instance, ProblemFixed, Warning, main

_ = Translation('univention-management-console-module-diagnostic').translate


run_descr: List[str] = ["messages for log"]
title: str = _("short description")
description: str = _("long HTML description")

# Optional: links to UMC modules - shown on any error when declared here global
umc_modules: List[Dict[str, Any]] = [
	{
		"module": "udm",
		"flavor": "navigation",
		"props": {
			"openObject": {
				'objectDN': 'uid=Administrator,cn=users,dc=foo,dc=bar',
				'objectType': 'users/user',
			}
		},
	},
]
# Optional: links to URLs - shown on any error when declared here globally
links: List[Dict[str, str]] = [
	{
		"name": "…",
		"href": "https://…",
		"label": _("…"),
	},
]
# Optional: actions buttons - shown on any error when declared here globally
buttons: List[Dict[str, str]] = [
	{
		"action": "action",
		"label": _("…"),
	},
]


def run(_umc_instance: Instance) -> Optional[Dict[str, Any]]:
	"""Required: Main entry point for UMC diagnostics plugin."""
	...
	raise Critical(description=_("…"), buttons=buttons)


def button_handler(umc_instance: Instance) -> Optional[Dict[str, Any]]:
	"""Optional: Handle button press."""
	...
	return run(umc_instance)


# Optional: map action name to Python callback function
actions: Dict[str, Callable[[Instance], Optional[Dict[str, Any]]] = {
	"action": button_handler,
}


if __name__ == '__main__':
	main()
```

Structure
---------

See [`plugins/__init__.py`](umc/python/diagnostic/__init__.py).

These global variables should always be set;
- `title`: A short description of the problem.
- `description`: A more detailed description of the problem. HTML allowed.

Other global variables are optional:
- `run_descr`: List of lines getting only printed to log file before each.
- `links`: Regular links.
- `buttons`: List of buttons to display under description.
- `umc_modules`: Links to other UMC modules.

By default these *links* and *buttons* and *modules* will always be shown when declared at the module level.
To only show them in some cases raise an exception `Problem` and pass them as additional arguments, e.g.

```python
raise Problem(
	description="Some error occured, see {link}",
	buttons=[{"action": "…", "label": _("…")}],
	links=[{"name": "link", "href": "…", "label": _("…")}],
)
```

- `run(_umc_instance)` is the main function, which is the starting point when invoked from UMC.
- May raise `Success` or `Conflict` or `Warning` or `Critical` or `ProblemFixed` or return a dictionary.

Notes
-----

- false positives should be avoided as much as possible as they easily lead to extra support cases.
