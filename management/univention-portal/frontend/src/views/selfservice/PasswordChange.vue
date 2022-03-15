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
  <site
    :title="TITLE"
    :subtitle="SUBTITLE"
  >
    <my-form
      ref="form"
      v-model="formValues"
      :widgets="formWidgets"
    >
      <footer>
        <button
          type="button"
          @click.prevent="cancel"
        >
          {{ CANCEL }}
        </button>
        <button
          type="submit"
          class="primary"
          @click.prevent="finish"
        >
          {{ CHANGE_PASSWORD }}
        </button>
      </footer>
    </my-form>
  </site>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import _ from '@/jsHelper/translate';
import MyForm from '@/components/forms/Form.vue';
import Site from '@/views/selfservice/Site.vue';
import { allValid, isEmpty, validateAll, WidgetDefinition } from '@/jsHelper/forms';
import { changePassword } from '@/jsHelper/umc';

interface FormValues {
  oldPassword: string,
  newPassword: string,
  newPasswordRetype: string,
}

interface ChangePasswordData {
  formWidgets: WidgetDefinition[],
  formValues: FormValues,
}

export default defineComponent({
  name: 'PasswordChange',
  components: {
    MyForm,
    Site,
  },
  data(): ChangePasswordData {
    return {
      formWidgets: [{
        type: 'PasswordBox',
        name: 'oldPassword',
        label: _('Old password'),
        validators: [(widget, value) => (
          isEmpty(widget, value) ? _('Please enter your old password') : ''
        )],
      }, {
        type: 'PasswordBox',
        name: 'newPassword',
        label: _('New password'),
        validators: [(widget, value) => (
          isEmpty(widget, value) ? _('Please enter your new password') : ''
        )],
      }, {
        type: 'PasswordBox',
        name: 'newPasswordRetype',
        label: _('New password (retype)'),
        validators: [(widget, value) => (
          isEmpty(widget, value) ? _('Please confirm your new password') : ''
        ), (widget, value, widgets, values) => {
          if (values.newPassword !== value) {
            return _('The new passwords do not match');
          }
          return '';
        }],
      }],
      formValues: {
        oldPassword: '',
        newPassword: '',
        newPasswordRetype: '',
      },
    };
  },
  computed: {
    TITLE(): string {
      return _('Change password');
    },
    SUBTITLE(): string {
      return _('Change your password');
    },
    CANCEL(): string {
      return _('Cancel');
    },
    CHANGE_PASSWORD(): string {
      return _('Change password');
    },
    form(): typeof MyForm {
      return this.$refs.form as typeof MyForm;
    },
  },
  mounted(): void {
    // FIXME (would like to get rid of setTimeout)
    // when this site is opening via a SideNavigation.vue entry then
    // 'activity/setRegion', 'portal-header' is called when SideNavigation is closed
    // which calls focusElement which uses setTimeout, 50
    // so we have to also use setTimeout
    setTimeout(() => {
      this.form.focusFirstInteractable();
    }, 100);
  },
  methods: {
    finish() {
      validateAll(this.formWidgets, this.formValues);
      if (!allValid(this.formWidgets)) {
        this.form.focusFirstInvalid();
        return;
      }
      this.$store.dispatch('activateLoadingState');
      changePassword(this.formValues.oldPassword, this.formValues.newPassword)
        .then((response) => {
          this.$store.dispatch('notifications/addSuccessNotification', {
            title: _('Change password'),
            description: response.message,
          });
          this.$store.dispatch('deactivateLoadingState');
          this.$router.push({ name: 'portal' });
        })
        .catch((error) => {
          console.error('Error while changing password', error);
          this.$store.dispatch('notifications/addErrorNotification', {
            title: _('Change password'),
            description: error.message,
          });
          this.$store.dispatch('deactivateLoadingState');
        });
    },
    cancel() {
      this.$router.push({ name: 'portal' });
    },
  },
});
</script>
<style lang="stylus">
.change-password
  input
    width: 100%
</style>
