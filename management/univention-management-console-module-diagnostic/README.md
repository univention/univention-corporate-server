UMC diagnostics module
======================

Put new Python module into directory [plugins/](umc/python/diagnostic/plugins/).

Template
--------

```python
#!/usr/bin/python3
# coding: utf-8

from typing import Dict, List

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

from univention.management.console.modules.diagnostic import MODULE, Critical, Instance, ProblemFixed, Warning, main


run_descr: List[str] = ["…"]  # for logging
title: str = _("short description")
description: str = _("long description")
umc_modules: List[Dict[str, str]] = [
	{
		"module": "udm",
		"flavor": "navigation",
	},
]
links: List[Dict[str, str]] = [
	{
		"name": "…",
		"href": "https://…",
		"label": _("…"),
		"title": _("…"),
	},
]
buttons: List[Dict[str, str]] = [
	{
		"action": "action",
		"name": "…",
		"label": _("…"),
	},
]
actions: Dict[str, Callable[[Instance], None] = {
	"action": button_handler,
}


def button_handler(umc_instance: Instance):
	"""Handle button press."""
	...
	return run(umc_instance)


def run(_umc_instance: Instance) -> None:
	"""Main entry point for UMC diagnostics plugin."""
	...
	raise Critical(description=_("…"), buttons=buttons)


if __name__ == '__main__':
	main()
```

Structure
---------

See [`plugins/__init__.py`](umc/python/diagnostic/__init__.py).

There are several global variables which do magic:

- `title`: A short description of the problem.
- `description`: A more detailed description of the problem.
- `run_descr`: List of lines getting printed to log file.
- `links`: Regular links.
- `buttons`: List of buttons to display under description.
- `umc_modules`: Links to other UMC modules.
- `run(_umc_instance)` is the main function, which is the starting point when invoked from UMC.
- Should raise `Success` or `Conflict` or `Warning` or `Critical` or `ProblemFixed`.
