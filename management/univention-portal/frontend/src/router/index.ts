/*
  * SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  * SPDX-License-Identifier: AGPL-3.0-only
  */

import { createRouter, createWebHashHistory } from 'vue-router';
import Portal from '@/views/Portal.vue';
import NotFound from '@/views/NotFound.vue';
import PasswordChange from '@/views/selfservice/PasswordChange.vue';
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
        path: 'selfservice/passwordchange',
        component: PasswordChange,
        name: 'selfservicePasswordChange',
      },
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
        props: (route) => ({ queryParamUsername: route.query.username, queryParamToken: route.query.token }),
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
        props: (route) => ({ queryParamUsername: route.query.username, queryParamToken: route.query.token }),
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
