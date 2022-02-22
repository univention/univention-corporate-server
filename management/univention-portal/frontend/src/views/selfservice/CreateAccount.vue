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
  <site
    :title="TITLE"
    subtitle=""
    :ucr-var-for-frontend-enabling="'umc/self-service/account-registration/frontend/enabled'"
  >
    <my-form
      v-if="formWidgets.length > 0"
      ref="form"
      v-model="formValues"
      :widgets="formWidgets"
    >
      <footer>
        <button
          type="submit"
          class="primary"
          @click.prevent="submit"
        >
          {{ SUBMIT_LABEL }}
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

import { umcCommandWithStandby } from '@/jsHelper/umc';
import Site from '@/views/selfservice/Site.vue';
import MyForm from '@/components/forms/Form.vue';
import ErrorDialog from '@/views/selfservice/ErrorDialog.vue';
import { allValid, validateAll, WidgetDefinition } from '@/jsHelper/forms';

interface Data {
  formValues: Record<string, string>,
  formWidgets: WidgetDefinition[],
}

export default defineComponent({
  name: 'CreateAccount',
  components: {
    Site,
    MyForm,
    ErrorDialog,
  },
  data(): Data {
    return {
      formValues: {},
      formWidgets: [],
    };
  },
  computed: {
    TITLE(): string {
      return _('Create an account');
    },
    SUBMIT_LABEL(): string {
      return this.TITLE;
    },
    form(): typeof MyForm {
      return this.$refs.form as typeof MyForm;
    },
    errorDialog(): typeof ErrorDialog {
      return this.$refs.errorDialog as typeof ErrorDialog;
    },
  },
  mounted() {
    umcCommandWithStandby(this.$store, 'passwordreset/get_registration_attributes')
      .then((result) => {
        result.layout.forEach((name) => {
          result.widget_descriptions.forEach((widget) => {
            if (widget.id !== name) {
              return;
            }
            this.formValues[widget.id] = '';
            this.formWidgets.push({
              type: widget.type === 'PasswordInputBox' ? 'PasswordBox' : widget.type,
              name: widget.id,
              label: widget.label,
              invalidMessage: '',
              required: widget.required,
            });
          });
        });
        this.$nextTick(() => {
          this.form.focusFirstInteractable();
        });
      })
      .catch((error) => {
        this.errorDialog.showError(error.message);
      });
  },
  methods: {
    submit() {
      if (!validateAll(this.formWidgets, this.formValues)) {
        this.form.focusFirstInvalid();
        return;
      }
      umcCommandWithStandby(this.$store, 'passwordreset/create_self_registered_account', {
        attributes: this.formValues,
      })
        .then((result) => {
          if (result.success) {
            if (result.verifyTokenSuccessfullySend) {
              this.$store.dispatch('notifications/addSuccessNotification', {
                title: _('Hello, %(username)s', { username: result.data.username }),
                description: _('We have sent you an email to %(email)s. Please follow the instructions in the email to verify your account.', { email: result.data.email }),
              });
              this.$router.push({ name: 'selfserviceVerifyAccount', query: { username: result.data.username } });
            } else {
              this.errorDialog.showError([
                _('Hello, %(username)s', { username: result.data.username }),
                _('An error occurred while sending the verification token for your account. Please request a new one.'),
              ])
                .then(() => {
                  this.$router.push({ name: 'selfserviceVerifyAccount', query: { username: result.data.username } });
                });
            }
          } else if (result.failType === 'INVALID_ATTRIBUTES') {
            Object.entries(result.data).forEach(([name, info]: [string, any]) => {
              if (info.isValid) {
                return;
              }
              this.formWidgets.forEach((widget) => {
                if ((widget.name) !== name) {
                  return;
                }
                widget.invalidMessage = info.message;
              });
            });
            if (!allValid(this.formWidgets)) {
              this.form.focusFirstInvalid();
            }
          } else if (result.failType === 'CREATION_FAILED') {
            this.errorDialog.showError([
              _('Creating a new user failed.'),
              result.data,
            ])
              .then(() => {
                this.form.focusFirstInteractable();
              });
          }
        });
    },
  },
});
</script>
