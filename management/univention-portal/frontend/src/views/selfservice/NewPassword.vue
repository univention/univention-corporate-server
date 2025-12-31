<!--
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
-->
<template>
  <site
    :title="TITLE"
    :subtitle="SUBTITLE"
  >
    <my-form
      id="new-password"
      ref="form"
      v-model="formValues"
      :widgets="formWidgetsWithTabindex"
    >
      <footer>
        <button
          type="submit"
          :tabindex="tabindex"
          class="button--primary"
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
}

export default defineComponent({
  name: 'NewPassword',
  components: {
    MyForm,
    Site,
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
      ), (widget, value, widgets, values) => {
        if (values.newPassword !== value) {
          return _('The new passwords do not match');
        }
        return '';
      }],
    }];
    return {
      formValues: {
        username: this.queryParamUsername,
        token: this.queryParamToken,
        newPassword: '',
        newPassword2: '',
      },
      formWidgets,
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
    errorDialog(): typeof ErrorDialog {
      return this.$refs.errorDialog as typeof ErrorDialog;
    },
    tabindex(): number {
      return activity(['selfservice'], this.activityLevel);
    },
    visibleWidgets(): WidgetDefinition[] {
      return this.formWidgets.filter((widget) => {
        if (widget.name === 'username') {
          return this.queryParamUsername === '';
        }
        if (widget.name === 'token') {
          return this.queryParamToken === '';
        }
        return true;
      });
    },
    formWidgetsTranslated(): WidgetDefinition[] {
      return this.visibleWidgets.map((widget) => {
        switch (widget.name) {
          case 'username':
            widget.label = _('Username');
            break;
          case 'token':
            widget.label = _('Token');
            break;
          case 'newPassword':
            widget.label = _('New password');
            break;
          case 'newPassword2':
            widget.label = _('New password (retype)');
            break;
          default:
            break;
        }
        return widget;
      });
    },
    formWidgetsWithTabindex(): WidgetDefinition[] {
      return this.formWidgetsTranslated.map((widget) => {
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
      this.form.focusFirstInteractable();
    }, 100);
  },
  methods: {
    submit() {
      if (!validateAll(this.visibleWidgets, this.formValues)) {
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
          this.errorDialog.showError(_('Your password has been successfully changed.'), _('Password change successful'), 'dialog')
            .then(() => {
              this.$router.push({ name: 'portal' });
            });
        })
        .catch((error) => {
          this.errorDialog.showError(error.message)
            .then(() => {
              this.form.focusFirstInteractable();
            });
        })
        .finally(() => {
          this.$store.dispatch('deactivateLoadingState');
        });
    },
  },
});
</script>
