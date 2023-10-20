import os
import pickle
import time

from univention.testing import utils


SHARE_CACHE_DIR = '/var/cache/univention-quota/'
TIMEOUT = 5  # seconds


def cache_must_exists(dn):
    filename = os.path.join(SHARE_CACHE_DIR, dn)
    i = 0
    while not os.path.exists(filename):
        if i > TIMEOUT:
            utils.fail(f'{filename} does not exist')
        print('Waiting for quota cache removing (%d) ...' % i)
        time.sleep(1)
        i += 1


def cache_must_not_exists(dn):
    filename = os.path.join(SHARE_CACHE_DIR, dn)
    i = 0
    while os.path.exists(filename):
        if i > TIMEOUT:
            utils.fail(f'{filename} exists')
            break
        print('Waiting for quota cache creating (%d) ...' % i)
        time.sleep(1)
        i += 1


def get_cache_values(dn):
    filename = os.path.join(SHARE_CACHE_DIR, dn)
    if not os.path.exists(filename):
        utils.fail(f'{filename} does not exist')
        return None

    with open(filename, 'rb') as fd:
        dn, attrs, policy_result = pickle.load(fd)  # noqa: S301

    share = {
        'univentionSharePath': attrs['univentionSharePath'][0],
        'inodeSoftLimit': policy_result.get('univentionQuotaSoftLimitInodes', [None])[0],
        'inodeHardLimit': policy_result.get('univentionQuotaHardLimitInodes', [None])[0],
        'spaceSoftLimit': policy_result.get('univentionQuotaSoftLimitSpace', [None])[0],
        'spaceHardLimit': policy_result.get('univentionQuotaHardLimitSpace', [None])[0],
        'reapplyQuota': policy_result.get('univentionQuotaReapplyEveryLogin', [None])[0],
    }
    return {key: value.decode('UTF-8') if isinstance(value, bytes) else value for key, value in share.items()}


def check_values(dn, inodeSoftLimit, inodeHardLimit, spaceSoftLimit, spaceHardLimit, reapplyQuota):
    cache = get_cache_values(dn)

    # if cache['univentionSharePath'] != path:
    #     utils.fail('univentionSharePath is set to %s. Expected: %s' % (cache['univentionSharePath'], path))
    print(cache)
    if cache['inodeSoftLimit'] != inodeSoftLimit:
        utils.fail(f'inodeSoftLimit is set to {cache["inodeSoftLimit"]}. Expected: {inodeSoftLimit}')
    if cache['inodeHardLimit'] != inodeHardLimit:
        utils.fail(f'inodeHardLimit is set to {cache["inodeHardLimit"]}. Expected: {inodeHardLimit}')
    if cache['spaceSoftLimit'] != spaceSoftLimit:
        utils.fail(f'spaceSoftLimit is set to {cache["spaceSoftLimit"]}. Expected: {spaceSoftLimit}')
    if cache['spaceHardLimit'] != spaceHardLimit:
        utils.fail(f'spaceHardLimit is set to {cache["spaceHardLimit"]}. Expected: {spaceHardLimit}')
    if cache['reapplyQuota'] != reapplyQuota:
        utils.fail(f'reapplyQuota is set to {cache["reapplyQuota"]}. Expected: {reapplyQuota}')
