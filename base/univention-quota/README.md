# univention-quota
UCS - set default-quotas for users

## univention-quota
This package can set default-quotas for a user at login. The quotas are set by resolving the shares corresponding to a local filesystem an look which policies are set for this share. Quotas are only set if the filesystem supports them and they are not already set for this user.

## univention-management-console-module-quota
This package contains the UMC module for the filesystem quota
