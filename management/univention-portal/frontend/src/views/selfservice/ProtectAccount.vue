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
    :ucr-var-for-frontend-enabling="'umc/self-service/protect-account/frontend/enabled'"
    path="passwordreset/get_contact"
    :guarded-widgets="widgets"
    @loaded="loaded"
    @save="setContactInfo"
  />
</template>

<script lang="ts">
import { defineComponent } from 'vue';

import { umcCommandWithStandby } from '@/jsHelper/umc';
import _ from '@/jsHelper/translate';
import GuardedSite from '@/views/selfservice/GuardedSite.vue';
import { WidgetDefinition } from '@/jsHelper/forms';

interface ContactInfo {
  id: string,
  label: string,
  value: string,
}

interface Data {
  contactInformation: ContactInfo[],
}

export default defineComponent({
  name: 'ProtectAccount',
  components: {
    GuardedSite,
  },
  data(): Data {
    return {
      contactInformation: [],
    };
  },
  computed: {
    TITLE(): string {
      return _('Protect account');
    },
    SUBTITLE(): string {
      return _('Everyone forgets his password now and then. Protect yourself and activate the opportunity to set a new password.');
    },
    widgets(): WidgetDefinition[] {
      return this.contactInformation.map((info) => ({
        type: 'TextBox',
        name: info.id,
        label: info.label,
        invalidMessage: '',
        required: true,
      }));
    },
  },
  methods: {
    loaded(result: ContactInfo[], formValues) {
      this.contactInformation = result;
      this.contactInformation.forEach((info) => {
        formValues[info.id] = info.value;
      });
    },
    setContactInfo(values) {
      umcCommandWithStandby(this.$store, 'passwordreset/set_contact', values)
        .then((result) => {
          let description = _('Your contact data has been successfully changed.');
          if (result.verificationEmailSend) {
            description = `${description}. ${_('Your account has to be verified again after changing your email. We have sent you an email to %(email)s. Please follow the instructions in the email to verify your account.', { email: result.email })}`;
          }
          this.$store.dispatch('notifications/addSuccessNotification', {
            title: _('Save successful'),
            description,
          });
          this.$router.push({ name: 'portal' });
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
