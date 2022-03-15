<!--
  Copyright 2021-2022 Univention GmbH

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
    path="passwordreset/get_contact"
    :guarded-widgets="formWidgets"
    @loaded="loaded"
    @save="setContactInfo"
  />
</template>

<script lang="ts">
import { defineComponent } from 'vue';

import { umcCommandWithStandby } from '@/jsHelper/umc';
import _ from '@/jsHelper/translate';
import GuardedSite from '@/views/selfservice/GuardedSite.vue';
import { initialValue, isEmpty, WidgetDefinition } from '@/jsHelper/forms';

interface ContactInfo {
  id: string,
  label: string,
  value: string,
}

interface Data {
  formWidgets: WidgetDefinition[],
}

export default defineComponent({
  name: 'ProtectAccount',
  components: {
    GuardedSite,
  },
  data(): Data {
    return {
      formWidgets: [],
    };
  },
  computed: {
    TITLE(): string {
      return _('Protect account');
    },
    SUBTITLE(): string {
      return _('Add or update your account recovery options.');
    },
  },
  methods: {
    loaded(result: ContactInfo[], formValues) {
      const widgets: WidgetDefinition[] = [];
      result.forEach((info) => {
        const widget: WidgetDefinition = {
          type: 'TextBox',
          name: info.id,
          label: info.label,
        };
        const retype: WidgetDefinition = {
          type: 'TextBox',
          name: `${info.id}--retype`,
          label: `${info.label} (retype)`,
          validators: [(_widget, _value) => (
            isEmpty(_widget, _value) ? _('Please confirm your %(label)s', { label: info.label }) : ''
          ), (_widget, _value, _widgets, _values) => {
            if (_values[widget.name] !== _value) {
              return _('The inputs do not match');
            }
            return '';
          }],
        };
        widgets.push(widget);
        widgets.push(retype);
        formValues[widget.name] = initialValue(widget, info.value);
        formValues[retype.name] = initialValue(retype, info.value);
      });
      this.formWidgets = widgets;
    },
    setContactInfo(values) {
      umcCommandWithStandby(this.$store, 'passwordreset/set_contact', values)
        .then((result) => {
          let description = _('Your account recovery options have been updated.');
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
