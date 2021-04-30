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
  store.dispatch('activateLoadingState');
  try {
    const response = await udmAdd(objectType, attrs);
    const result = response.data.result[0];
    if (!result.success) {
      throw new Error(result.details);
    }
    return result.$dn$;
  } catch (err) {
    console.error(err.message);
    store.dispatch('notificationBubble/addErrorNotification', {
      bubbleTitle: translate(errorMessage),
    });
  }
  return '';
}

async function put(dn, attrs, store, successMessage, errorMessage) {
  try {
    const response = await udmPut(dn, attrs);
    const result = response.data.result[0];
    if (!result.success) {
      throw new Error(result.details);
    }
    store.dispatch('notificationBubble/addSuccessNotification', {
      bubbleTitle: translate(successMessage),
    });
    await store.dispatch('portalData/waitForChange', {
      retries: 10,
      adminMode: true,
    });
    await store.dispatch('loadPortal', { adminMode: true });
  } catch (err) {
    console.error(err.message);
    store.dispatch('notificationBubble/addErrorNotification', {
      bubbleTitle: translate(errorMessage),
    });
  }
}

export { put, add };
