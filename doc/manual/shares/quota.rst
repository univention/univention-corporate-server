.. _shares-quota:

Configuration of file system quota
==================================

UCS allows the limiting of the storage space available to a user on a
partition. These thresholds can be set as either a quantity of storage
space (e.g., 500 MB per user) or a maximum number of files without a
defined size limit.

Two types of thresholds are differentiated:

Hard limit
   The *hard limit* is the maximum storage space a user can employ. If it is
   attained, no further files can be saved.

Soft limit
   If the *soft limit* is attained - which must be smaller than the hard limit -
   and the storage space used is still below the hard limit, the user is given a
   grace period of seven days to delete unused data. Once seven days have
   elapsed, it is no longer possible to save or change additional files. A
   warning is displayed to users who access a file system with an exceeded quota
   via CIFS (the threshold is based on the soft limit).

If a quota value of ``0`` has been configured, it is evaluated as an unlimited
quota.

Quotas can either be defined via the UMC module :guilabel:`Filesystem quotas` or
a policy for shares, see :ref:`shares-quota-policy`.

File system quotas can only be applied on partitions with the file systems
``ext4`` and ``XFS``. Before filesystem quotas can be configured, the use of
file system quotas needs to be activated per partition, see
:ref:`shares-quota-umc`.

.. _shares-quota-umc:

Activating filesystem quota
---------------------------

In the UMC module :guilabel:`Filesystem quotas`, all the
partitions are listed on which quotas can be set up. Only partitions are
shown which are currently mounted under a mount point.

.. _shares-quota-figure:

.. figure:: /images/quota-overview.*
   :alt: The UMC module *File system quotas*

   The UMC module :guilabel:`File system quotas`

The current quota status (activated/deactivated) is shown and can be changed
with *Activate* and *Deactivate*.

If quota has been activated on a ``XFS`` root-partition, the system has to be
rebooted.

.. _shares-quota-policy:

Configuring filesystem quota
----------------------------

Quotas can either be defined via the UMC module :guilabel:`Filesystem quotas` or
a policy for shares, see :ref:`central-policies`. The configuration through a
policy allows setting a default value for all users, while the UMC module allows
easy configuration of user-specific quota values.

The user-specific quota settings can be configured with the UMC module
:guilabel:`Filesystem quotas`. The permitted storage quantities can be set with
the pencil symbol for all enabled partitions. All the settings are set
user-specifically. :guilabel:`Add` can be used to set the thresholds for soft
and hard limits for a user.

The quota settings can also be set with a *User quota* share policy. The
settings apply for all users of a share; it is not possible to establish
different quota limits for different users within one policy.

Quota settings that are applied via a quota policy are by default only applied
once to the filesystem. If the setting is changed, it will not be applied
automatically on the next user login. To inherit changed quota values, the
option *Reapply settings on every login* can be activated at the quota policy.

Quota policies can only be used on partitions for which the quota support is
enabled in the UMC module, see :ref:`shares-quota-umc`.

.. note::

   Filesystem quotas always apply to a full partition. Even if the
   policies are defined for shares, they are used on complete
   partitions. If, for example, three shares are provided on one server
   which are all saved on the separate :file:`/var/` partition and three different
   policies are configured and used, the most restrictive setting
   applies for the complete partition. If different quotas are used, it
   is recommended to distribute the data over individual partitions.

.. _shares-quota-apply:

Evaluation of quota during login
--------------------------------

The settings defined in the UCS management system are evaluated and
enabled during login to UCS systems by the tool
:command:`univention-user-quota` run in the PAM stack.

If no quota are needed, the evaluation can be disabled by setting the
|UCSUCRV| :envvar:`quota/userdefault` to ``no``.

If the |UCSUCRV| :envvar:`quota/logfile` is set to any file name,
the activation of the quotas is logged in the specified file.

.. _shares-quota-query:

Querying the quota status by administrators or users
----------------------------------------------------

A user can view the quota limits defined for a system using the command
:command:`repquota -va`, e.g.:

.. code-block:: console

   *** Report for user quotas on device /dev/vdb1
   Block grace time: 7days; Inode grace time: 7days
                           Block limits                File limits
   User            used    soft    hard  grace    used  soft  hard  grace
   ----------------------------------------------------------------------
   root            --      20       0       0              2     0     0
   Administrator   --       0       0  102400              0     0     0
   user01          --  234472 2048000 4096000              2     0     0
   user02          --       0 2048000 4096000              0     0     0

   Statistics:
   Total blocks: 8
   Data blocks: 1
   Entries: 4
   Used average: 4.000000

Logged in users can use the :command:`quota -v` command to view the applicable
quota limits and the current utilization.

Further information on the commands can be found in the man pages of the
commands.
