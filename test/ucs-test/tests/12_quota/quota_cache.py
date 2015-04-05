import univention.testing.utils as utils
import cPickle
import os

SHARE_CACHE_DIR = '/var/cache/univention-quota/'


def get_cache_values(dn):
	filename = os.path.join(SHARE_CACHE_DIR, dn)
	if not os.path.exists(filename):
		utils.fail('%s does not exist' % filename)
		return None

	f = open(filename, 'r')
	dn, attrs, policy_result = cPickle.load(f)
	f.close()

	share = {}
	share['univentionSharePath'] = attrs['univentionSharePath'][0]
	share['inodeSoftLimit'] = policy_result.get('univentionQuotaSoftLimitInodes', [None])[0]
	share['inodeHardLimit'] = policy_result.get('univentionQuotaHardLimitInodes', [None])[0]
	share['spaceSoftLimit'] = policy_result.get('univentionQuotaSoftLimitSpace', [None])[0]
	share['spaceHardLimit'] = policy_result.get('univentionQuotaHardLimitSpace', [None])[0]
	share['reapplyQuota'] = policy_result.get('univentionQuotaReapplyEveryLogin', [None])[0]

	return share


def check_values(dn, inodeSoftLimit, inodeHardLimit, spaceSoftLimit, spaceHardLimit, reapplyQuota):
	cache = get_cache_values(dn)

	#if cache['univentionSharePath'] != path:
	#	utils.fail('univentionSharePath is set to %s. Expected: %s' % (cache['univentionSharePath'], path))
	print cache
	if cache['inodeSoftLimit'] != inodeSoftLimit:
		utils.fail('inodeSoftLimit is set to %s. Expected: %s' % (cache['inodeSoftLimit'], inodeSoftLimit))
	if cache['inodeHardLimit'] != inodeHardLimit:
		utils.fail('inodeHardLimit is set to %s. Expected: %s' % (cache['inodeHardLimit'], inodeHardLimit))
	if cache['spaceSoftLimit'] != spaceSoftLimit:
		utils.fail('spaceSoftLimit is set to %s. Expected: %s' % (cache['spaceSoftLimit'], spaceSoftLimit))
	if cache['spaceHardLimit'] != spaceHardLimit:
		utils.fail('spaceHardLimit is set to %s. Expected: %s' % (cache['spaceHardLimit'], spaceHardLimit))
	if cache['reapplyQuota'] != reapplyQuota:
		utils.fail('reapplyQuota is set to %s. Expected: %s' % (cache['reapplyQuota'], reapplyQuota))
