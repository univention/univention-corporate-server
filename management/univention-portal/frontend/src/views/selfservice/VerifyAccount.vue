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
  >
    <my-form
      ref="form"
      v-model="formValues"
      :widgets="formWidgetsWithTabindex"
    >
      <footer>
        <button
          v-if="formValues.username && formValues.token"
          type="submit"
          :tabindex="tabindex"
          class="primary"
          @click.prevent="verifyAccount"
        >
          {{ VERIFY_ACCOUNT }}
        </button>
        <button
          v-else
          type="submit"
          :tabindex="tabindex"
          @click.prevent="requestNewToken"
        >
          {{ REQUEST_NEW_TOKEN }}
        </button>
      </footer>
    </my-form>
    <error-dialog
      ref="errorDialog"
    />
  </site>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import _ from '@/jsHelper/translate';

import Site from '@/views/selfservice/Site.vue';
import { validateAll, WidgetDefinition } from '@/jsHelper/forms';
import { umcCommandWithStandby } from '@/jsHelper/umc';
import MyForm from '@/components/forms/Form.vue';
import ErrorDialog from '@/views/selfservice/ErrorDialog.vue';
import { mapGetters } from 'vuex';
import activity from '@/jsHelper/activity';

interface FormData {
  username: string,
  token: string,
}

interface Data {
  formValues: FormData,
  formWidgets: WidgetDefinition[],
  failType: string,
  successType: string,
}

export default defineComponent({
  name: 'VerifyAccount',
  components: {
    Site,
    MyForm,
    ErrorDialog,
  },
  props: {
    queryParamUsername: {
      type: String,
      default: '',
    },
    queryParamToken: {
      type: String,
      default: '',
    },
  },
  data(): Data {
    return {
      formValues: {
        username: this.queryParamUsername,
        token: this.queryParamToken,
      },
      failType: '',
      successType: '',
      formWidgets: [{
        type: 'TextBox',
        name: 'username',
        label: _('Username'),
        invalidMessage: '',
        required: true,
      }, {
        type: 'TextBox',
        name: 'token',
        label: _('Token'),
        invalidMessage: '',
        required: false,
      }],
    };
  },
  computed: {
    ...mapGetters({
      activityLevel: 'activity/level',
    }),
    TITLE(): string {
      return _('Account verification');
    },
    REQUEST_NEW_TOKEN(): string {
      return _('Request new token');
    },
    VERIFY_ACCOUNT(): string {
      return _('Verify account');
    },
    form(): typeof MyForm {
      return this.$refs.form as typeof MyForm;
    },
    errorDialog(): typeof ErrorDialog {
      return this.$refs.errorDialog as typeof ErrorDialog;
    },
    tabindex(): number {
      return activity(['selfservice'], this.activityLevel);
    },
    formWidgetsWithTabindex(): WidgetDefinition[] {
      return this.formWidgets.map((widget) => {
        widget.tabindex = this.tabindex;
        return widget;
      });
    },
  },
  watch: {
    queryParamUsername(value) {
      this.formValues.username = value;
    },
    queryParamToken(value) {
      this.formValues.token = value;
    },
  },
  mounted() {
    // FIXME (would like to get rid of setTimeout)
    // when this site is opening via a SideNavigation.vue entry then
    // 'activity/setRegion', 'portal-header' is called when SideNavigation is closed
    // which calls focusElement which uses setTimeout, 50
    // so we have to also use setTimeout
    setTimeout(() => {
      (this.$refs.form as typeof MyForm).focusFirstInteractable();
    }, 100);
  },
  methods: {
    requestNewToken() {
      if (!validateAll(this.formWidgets, this.formValues)) {
        this.form.focusFirstInvalid();
        return;
      }
      umcCommandWithStandby(this.$store, 'passwordreset/send_verification_token', {
        username: this.formValues.username,
      })
        .then((result) => {
          if (result.success) {
            this.errorDialog.showError([
              _('Hello %(username)s,', { username: result.data.username }),
              _('We have sent you an email to your registered address. Please follow the instructions in the email to verify your account.'),
            ], _('Verification token send'), 'dialog')
              .then(() => {
                this.form.focusFirstInteractable();
              });
          } else if (result.failType === 'INVALID_INFORMATION') {
            this.errorDialog.showError(_('The verification token could not be sent. Please verify your input.'), _('Failed to send verification token'))
              .then(() => {
                this.form.focusFirstInteractable();
              });
          }
        })
        .catch((error) => {
          this.errorDialog.showError(error.message)
            .then(() => {
              this.form.focusFirstInteractable();
            });
        });
    },
    verifyAccount() {
      if (!validateAll(this.formWidgets, this.formValues)) {
        this.form.focusFirstInvalid();
        return;
      }
      umcCommandWithStandby(this.$store, 'passwordreset/verify_contact', {
        username: this.formValues.username,
        token: this.formValues.token,
        method: 'verify_email',
      })
        .then((result) => {
          if (result.successType === 'VERIFIED') {
            this.$store.dispatch('notifications/addSuccessNotification', {
              title: _('Welcome, %(username)s', { username: result.data.username }),
              description: _('Your account has been successfully verified.'),
            });
            this.$router.push({ name: 'portal' });
          } else if (result.successType === 'ALREADY_VERIFIED') {
            this.$store.dispatch('notifications/addSuccessNotification', {
              title: _('Welcome, %(username)s', { username: result.data.username }),
              description: _('Your account has already been verified.'),
            });
            this.$router.push({ name: 'portal' });
          } else if (result.failType === 'INVALID_INFORMATION') {
            this.errorDialog.showError(_('The account could not be verified. Please verify your input.'), _('Verification failed'))
              .then(() => {
                this.form.focusFirstInteractable();
              });
            this.formValues.token = '';
          }
        })
        .catch((error) => {
          this.errorDialog.showError(error.message)
            .then(() => {
              this.form.focusFirstInteractable();
            });
          this.formValues.token = '';
        });
    },
  },
});
</script>
