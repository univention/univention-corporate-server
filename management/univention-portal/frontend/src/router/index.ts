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

import { createRouter, createWebHashHistory } from 'vue-router';
import Portal from '@/views/Portal.vue';
import NotFound from '@/views/NotFound.vue';
import Profile from '@/views/selfservice/Profile.vue';
import ProtectAccount from '@/views/selfservice/ProtectAccount.vue';
import CreateAccount from '@/views/selfservice/CreateAccount.vue';
import VerifyAccount from '@/views/selfservice/VerifyAccount.vue';
import PasswordForgotten from '@/views/selfservice/PasswordForgotten.vue';
import NewPassword from '@/views/selfservice/NewPassword.vue';
import ServiceSpecificPasswords from '@/views/selfservice/ServiceSpecificPasswords.vue';

const routes = [
  {
    path: '/',
    component: Portal,
    name: 'portal',

    children: [
      {
        path: 'selfservice/profile',
        component: Profile,
        name: 'selfserviceProfile',
      },
      {
        path: 'selfservice/createaccount',
        component: CreateAccount,
        name: 'selfserviceCreateAccount',
      },
      {
        path: 'selfservice/verifyaccount',
        component: VerifyAccount,
        name: 'selfserviceVerifyAccount',
      },
      {
        path: 'selfservice/protectaccount',
        component: ProtectAccount,
        name: 'selfserviceProtectAccount',
      },
      {
        path: 'selfservice/passwordforgotten',
        component: PasswordForgotten,
        name: 'selfservicePasswordForgotten',
      },
      {
        path: 'selfservice/newpassword',
        component: NewPassword,
        name: 'selfserviceNewPassword',
      },
      {
        path: 'selfservice/servicespecificpasswords',
        component: ServiceSpecificPasswords,
        name: 'selfserviceServiceSpecificPasswords',
      },
    ],
  },
  { path: '/:pathMatch(.*)*', component: NotFound },
];

// eslint-disable-next-line import/prefer-default-export
export const router = createRouter({
  history: createWebHashHistory(),
  routes,
});
