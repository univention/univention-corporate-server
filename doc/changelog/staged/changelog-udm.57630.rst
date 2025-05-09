UDM syntax extensions are now loaded in an isolated namespace, preventing extensions from overwriting names used by other syntax extensions.
Syntax extension files now must import the modules and syntax classes they use instead of relying on names implicitly available in ``univention.admin.syntax``.
