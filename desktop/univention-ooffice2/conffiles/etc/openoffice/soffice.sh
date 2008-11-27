@%@BCWARNING=# @%@
# configuration file to set up some environment variables for OOo

# File locking; possible values are:
# - yes:  enable file locking unconditionally
# - no:   disable file locking
# - auto: enable file locking, when the document is found on a nfs share
# If the environment variable SAL_ENABLE_FILE_LOCKING is set,
# the setting if ENABLE_FILE_LOCKING has no effect.

export FILE_LOCKING=@%@openoffice/filelocking@%@

# OpenGL support; may cause trouble with the restricted nvidia and fglrx
# drivers; possible values are:
# - yes:  enable OpenGL support unconditionally
# - no:   disable OpenGL support.
# - auto: only enable OpenGL support, if not running with the restricted
#   nvidia and fglrx drivers.
# If the environment variable SAL_NOOPENGL is set,
# the setting if OPENGL_SUPPORT has no effect.

export OPENGL_SUPPORT=@%@openoffice/opengl@%@
