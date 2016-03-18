"""
Module for jenkinsapi Plugin
"""


class Plugin(object):

    """
    Plugin class
    """

    def __init__(self, plugin_dict):
        assert isinstance(plugin_dict, dict)
        self.__dict__ = plugin_dict

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __str__(self):
        return self.shortName

    def __repr__(self):
        return "<%s.%s %s>" % (
            self.__class__.__module__,
            self.__class__.__name__,
            str(self)
        )
