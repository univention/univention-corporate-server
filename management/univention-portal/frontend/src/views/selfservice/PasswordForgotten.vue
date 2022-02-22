<!--
  Copyright 2021 Univention GmbH

  https://www.univention.de/

  All rights reserved.

  The source code of this program is made available
  under the terms of the GNU Affero General Public License version 3
  (GNU AGPL V3) as published by the Free Software Foundation.

  Binary versions of this program provided by Univention to you as
  well as other copyrighted, protected or trademarked materials like
  Logos, graphics, fonts, specific documentations and configurations,
  cryptographic keys etc. are subject to a license agreement between
  you and Univention and not subject to the GNU AGPL V3.

  In the case you use this program under the terms of the GNU AGPL V3,
  the program is provided in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
  GNU Affero General Public License for more details.

  You should have received a copy of the GNU Affero General Public
  License with the Debian GNU/Linux or Univention distribution in file
  /usr/share/common-licenses/AGPL-3; if not, see
  <https://www.gnu.org/licenses/>.
-->
<template>
  <guarded-site
    ref="guardedSite"
    :title="TITLE"
    :subtitle="SUBTITLE"
    :ucr-var-for-frontend-enabling="'umc/self-service/passwordreset/frontend/enabled'"
    path="passwordreset/get_reset_methods"
    :password-needed="false"
    :guarded-widgets="widgets"
    @loaded="loaded"
    @save="sendToken"
  />
</template>

<script lang="ts">
import { defineComponent } from 'vue';

import { umcCommandWithStandby } from '@/jsHelper/umc';
import _ from '@/jsHelper/translate';
import GuardedSite from '@/views/selfservice/GuardedSite.vue';
import { WidgetDefinition } from '@/jsHelper/forms';

interface MethodInfo {
  id: string,
  label: string,
}

interface Data {
  methodInformation: MethodInfo[],
}

export default defineComponent({
  name: 'PasswordForgotten',
  components: {
    GuardedSite,
  },
  data(): Data {
    return {
      methodInformation: [],
    };
  },
  computed: {
    TITLE(): string {
      return _('Password forgotten');
    },
    SUBTITLE(): string {
      return _('Forgot your password? Set a new one:');
    },
    widgets(): WidgetDefinition[] {
      return [{
        type: 'RadioBox',
        name: 'method',
        options: this.methodInformation,
        label: _('Please choose an option to renew your password.'),
        invalidMessage: '',
        required: true,
      }];
    },
  },
  methods: {
    loaded(result: MethodInfo[], formValues) {
      this.methodInformation = result;
      formValues.method = '';
      if (result.length) {
        formValues.method = result[0].id;
      }
    },
    sendToken(values) {
      umcCommandWithStandby(this.$store, 'passwordreset/send_token', values)
        .then(() => {
          this.$store.dispatch('notifications/addSuccessNotification', {
            title: _('Token sent'),
            description: _('Successfully sent Token.'),
          });
          this.$router.push({ name: 'selfserviceNewPassword', query: { username: values.username } });
        })
        .catch((error) => {
          (this.$refs.guardedSite as typeof GuardedSite).showError(error.message)
            .then(() => {
              (this.$refs.guardedSite as typeof GuardedSite).refocus();
            });
        });
    },
  },
});
</script>
