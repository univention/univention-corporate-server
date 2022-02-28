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
    :subtitle="SUBTITLE"
  >
    <my-form
      ref="form"
      v-model="formValues"
      :widgets="formWidgetsWithTabindex"
    >
      <footer>
        <button
          type="submit"
          :tabindex="tabindex"
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

import { umcCommand } from '@/jsHelper/umc';
import _ from '@/jsHelper/translate';
import Site from '@/views/selfservice/Site.vue';
import MyForm from '@/components/forms/Form.vue';
import { validateAll, isEmpty, WidgetDefinition } from '@/jsHelper/forms';
import ErrorDialog from '@/views/selfservice/ErrorDialog.vue';
import activity from '@/jsHelper/activity';
import { mapGetters } from 'vuex';

interface FormData {
  username: string,
  token: string,
  newPassword: string,
  newPassword2: string,
}

interface Data {
  formValues: FormData,
  formWidgets: WidgetDefinition[],
  tokenGiven: boolean,
}

export default defineComponent({
  name: 'NewPassword',
  components: {
    MyForm,
    Site,
    ErrorDialog,
  },
  data(): Data {
    const formWidgets: WidgetDefinition[] = [{
      type: 'TextBox',
      name: 'username',
      label: _('Username'),
      readonly: false, // TODO
      invalidMessage: '',
      required: true,
    }, {
      type: 'TextBox',
      name: 'token',
      label: _('Token'),
      readonly: false, // TODO
      invalidMessage: '',
      required: true,
    }, {
      type: 'PasswordBox',
      name: 'newPassword',
      label: _('New password'),
      invalidMessage: '',
      required: true,
    }, {
      type: 'PasswordBox',
      name: 'newPassword2',
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
    }];
    return {
      formValues: {
        username: '',
        token: '',
        newPassword: '',
        newPassword2: '',
      },
      formWidgets,
      tokenGiven: false,
    };
  },
  computed: {
    ...mapGetters({
      activityLevel: 'activity/level',
    }),
    TITLE(): string {
      return _('Set new password');
    },
    SUBTITLE(): string {
      return '';
    },
    SUBMIT_LABEL(): string {
      return _('Change password');
    },
    form(): typeof MyForm {
      return this.$refs.form as typeof MyForm;
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
  mounted() {
    setTimeout(() => {
      if (typeof this.$route.query.username === 'string' && this.$route.query.username) {
        this.formValues.username = this.$route.query.username;
      }
      if (typeof this.$route.query.token === 'string' && this.$route.query.token) {
        this.formValues.token = this.$route.query.token;
        this.tokenGiven = true;
      }
      setTimeout(() => {
        this.form.focusFirstInteractable();
      }, 300); // TODO...
    }, 300); // TODO...
  },
  methods: {
    submit() {
      if (!validateAll(this.formWidgets, this.formValues)) {
        this.form.focusFirstInvalid();
        return;
      }
      const params = {
        username: this.formValues.username,
        token: this.formValues.token,
        password: this.formValues.newPassword,
      };
      this.$store.dispatch('activateLoadingState');
      umcCommand('passwordreset/set_password', params)
        .then(() => {
          this.$store.dispatch('notifications/addSuccessNotification', {
            title: _('Token sent'),
            description: _('Successfully sent Token.'),
          });
        })
        .catch((error) => {
          (this.$refs.errorDialog as typeof ErrorDialog).showError(error.message)
            .then(() => {
              (this.$refs.saveButton as HTMLButtonElement).focus();
            });
        })
        .finally(() => {
          this.$store.dispatch('deactivateLoadingState');
        });
    },
  },
});
</script>
