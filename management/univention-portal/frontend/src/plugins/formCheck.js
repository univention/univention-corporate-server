/*
 * SPDX-FileCopyrightText: 2021-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
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
