/*
 * SPDX-FileCopyrightText: 2021-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
import { User } from '@/store/modules/user/user.models';

function login(user: User): void {
  if (user.authMode === 'saml') {
    window.location.href = `/univention/saml/?location=${window.location.pathname}`;
  } else if (user.authMode === 'oidc') {
    window.location.href = `/univention/oidc/?location=${window.location.pathname}`;
  } else {
    window.location.href = `/univention/login/?location=${window.location.pathname}`;
  }
}

function logout(): void {
  window.location.href = `/univention/logout/?location=${window.location.pathname}`;
}

export { login, logout };
