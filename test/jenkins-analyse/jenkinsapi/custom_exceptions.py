"""Module for custom_exceptions.

Where possible we try to throw exceptions with non-generic,
meaningful names.
"""


class JenkinsAPIException(Exception):

    """Base class for all errors
    """


class NotFound(JenkinsAPIException):

    """Resource cannot be found
    """


class ArtifactsMissing(NotFound):

    """Cannot find a build with all of the required artifacts.
    """


class UnknownJob(KeyError, NotFound):

    """Jenkins does not recognize the job requested.
    """


class UnknownView(KeyError, NotFound):

    """Jenkins does not recognize the view requested.
    """


class UnknownNode(KeyError, NotFound):

    """Jenkins does not recognize the node requested.
    """


class UnknownQueueItem(KeyError, NotFound):

    """Jenkins does not recognize the requested queue item
    """


class UnknownPlugin(KeyError, NotFound):

    """Jenkins does not recognize the plugin requested.
    """


class NoBuildData(NotFound):

    """A job has no build data.
    """


class NotBuiltYet(NotFound):

    """A job has no build data.
    """


class ArtifactBroken(JenkinsAPIException):

    """An artifact is broken, wrong
    """


class TimeOut(JenkinsAPIException):

    """Some jobs have taken too long to complete.
    """


class NoResults(JenkinsAPIException):

    """A build did not publish any results.
    """


class FailedNoResults(NoResults):

    """A build did not publish any results because it failed
    """


class BadURL(ValueError, JenkinsAPIException):

    """A URL appears to be broken
    """


class NotAuthorized(JenkinsAPIException):

    """Not Authorized to access resource"""
    # Usually thrown when we get a 403 returned


class NotSupportSCM(JenkinsAPIException):

    """
    It's a SCM that does not supported by current version of jenkinsapi
    """


class NotConfiguredSCM(JenkinsAPIException):

    """It's a job that doesn't have configured SCM
    """


class NotInQueue(JenkinsAPIException):

    """It's a job that is not in the queue
    """


class PostRequired(JenkinsAPIException):

    """Method requires POST and not GET
    """


class BadParams(JenkinsAPIException):

    """Invocation was given bad or inappropriate params
    """


class AlreadyExists(JenkinsAPIException):

    """
    Method requires POST and not GET
    """
