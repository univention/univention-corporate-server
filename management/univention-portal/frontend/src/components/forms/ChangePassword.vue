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
  <modal-dialog
    :i18n-title-key="CHANGE_PASSWORD"
    class="change-password"
    @cancel="cancel"
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
          @click.prevent="finish"
        >
          {{ CHANGE_PASSWORD }}
        </button>
      </footer>
    </my-form>
  </modal-dialog>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import _ from '@/jsHelper/translate';
import MyForm from '@/components/forms/Form.vue';
import ModalDialog from '@/components/modal/ModalDialog.vue';
import { allValid, isEmpty, validateAll } from '@/jsHelper/forms';

interface ChangePasswordData {
  formWidgets: any[],
  formValues: any,
}

export default defineComponent({
  name: 'ChangePassword',
  components: {
    MyForm,
    ModalDialog,
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
        ), (widget, value) => {
          // @ts-ignore TODO
          if (this.formValues.newPassword !== value) {
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
    CANCEL(): string {
      return _('Cancel');
    },
    CHANGE_PASSWORD(): string {
      return _('Change password');
    },
  },
  mounted(): void {
    // @ts-ignore TODO
    this.$refs.form.focusFirstInteractable();
  },
  methods: {
    finish() {
      validateAll(this.formWidgets, this.formValues);
      if (!allValid(this.formWidgets)) {
        // @ts-ignore TODO
        this.$refs.form.focusFirstInvalid();
        return;
      }
      this.$store.dispatch('modal/resolve', {
        level: 1,
        oldPassword: this.formValues.oldPassword,
        newPassword: this.formValues.newPassword,
      });
    },
    cancel() {
      this.$store.dispatch('modal/hideAndClearModal');
    },
  },
});
</script>
<style lang="stylus">
.change-password
  input
    width: 100%
</style>
