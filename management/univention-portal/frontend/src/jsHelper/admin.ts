/*
 * Copyright 2021 Univention GmbH
 *
 * https://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <https://www.gnu.org/licenses/>.
 */

import { translate } from '@/i18n/translations';
import { udmPut, udmAdd } from '@/jsHelper/umc';

async function add(objectType, attrs, store, errorMessage): Promise<string> {
  try {
    const response = await udmAdd(objectType, attrs);
    const result = response.data.result[0];
    if (!result.success) {
      throw new Error(result.details);
    }
    return result.$dn$;
  } catch (err) {
    store.dispatch('notifications/addErrorNotification', {
      title: translate(errorMessage),
      description: err.message,
      hidingAfter: -1,
    });
  }
  return '';
}

async function put(dn, attrs, { dispatch }, successMessage, errorMessage): Promise<boolean> {
  try {
    const response = await udmPut(dn, attrs);
    const result = response.data.result[0];
    if (!result.success) {
      throw new Error(result.details);
    }
    dispatch('notifications/addSuccessNotification', {
      title: translate(successMessage),
      hidingAfter: -1,
    }, { root: true });
    await dispatch('portalData/waitForChange', {
      retries: 10,
      adminMode: true,
    }, { root: true });
    await dispatch('loadPortal', { adminMode: true }, { root: true });
    return true;
  } catch (err) {
    dispatch('notifications/addErrorNotification', {
      title: translate(errorMessage),
      description: err.message,
      hidingAfter: -1,
    }, { root: true });
    return false;
  }
}

// edit mode default settings
const adminState = process.env.VUE_APP_LOCAL ? (!!localStorage.getItem('UCSAdmin') || false) : false;

export { put, add, adminState };
