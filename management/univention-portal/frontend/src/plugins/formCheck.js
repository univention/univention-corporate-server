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
// plugins/formCheck

import { store } from '../store';

const formCheckPlugin = {
  install: (app) => {
    // plugin code
    const formChecker = (iData, iReqFields, iLabel) => {
      const iProps = Object.getOwnPropertyNames(iData);
      const modalError = store.getters['modal/getModalError'];
      let isObject = false;

      if (iProps) {
        let i = 0;
        for (i; i < iProps.length; i += 1) {
          if (typeof iData[iProps[i]] === typeof {}) {
            isObject = true;
          }
          if (!isObject && iReqFields && iReqFields.includes(iProps[i])) {
            if (iData && iData[iProps[i]] === '') {
              if (!modalError.includes(`${iLabel}_${[iProps[i]]}`)) {
                store.dispatch('modal/setModalError', `${iLabel}_${[iProps[i]]}`);
              }
            } else {
              store.dispatch('modal/removeModalErrorItem', `${iLabel}_${[iProps[i]]}`);
            }
          } else if (i < 1 && iData && iData[0]) {
            if (iData[0].value === '') {
              if (!modalError.includes(`${iLabel}_${iReqFields}`)) {
                store.dispatch('modal/setModalError', `${iLabel}_${iReqFields}`);
              }
            } else {
              store.dispatch('modal/removeModalErrorItem', `${iLabel}_${iReqFields}`);
            }
          }
        }
      }
      return true;
    };

    app.config.globalProperties.$formChecker = formChecker;
  },
};

export default formCheckPlugin;

// Usage examples:
// @blur="$formChecker(modelValueData, requiredFields, label)"
// @keyup="$formChecker(modelValueData, requiredFields, label)"

// @blur="$formChecker(modelValueData, currentLocale, _('Link'))"
// @keyup="$formChecker(modelValueData, currentLocale, _('Link'))"
