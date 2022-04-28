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
      ref="loginForm"
      v-model="loginValues"
      :widgets="loginWidgetsWithTabindex"
    >
      <footer v-if="!attributesLoaded">
        <button
          type="submit"
          :tabindex="tabindex"
          @click.prevent="onContinue"
        >
          {{ CONTINUE }}
        </button>
      </footer>
    </my-form>
    <my-form
      v-if="attributesLoaded"
      ref="attributesForm"
      v-model="attributeValues"
      :widgets="attributeWidgetsWithTabindex"
    >
      <footer
        v-if="renderDeregistration"
      >
        <button
          ref="deregistrationButton"
          type="button"
          :tabindex="tabindex"
          @click="deleteAccount"
        >
          {{ DELETE_ACCOUNT }}
        </button>
      </footer>
      <footer>
        <button
          type="button"
          :tabindex="tabindex"
          @click="close"
        >
          {{ CLOSE }}
        </button>
        <button
          ref="saveButton"
          type="submit"
          :tabindex="tabindex"
          class="primary"
          @click.prevent="onSave"
        >
          {{ SAVE }}
        </button>
      </footer>
    </my-form>
    <error-dialog
      ref="errorDialog"
    />
    <confirm-deregistration
      ref="confirmDeregistrationDialog"
    />
  </site>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

import isEmpty from 'lodash.isempty';
import isEqual from 'lodash.isequal';
import { umcCommand, umcCommandWithStandby } from '@/jsHelper/umc';
import { isTrue } from '@/jsHelper/ucr';
import {
  sanitizeBackendValues,
  sanitizeBackendWidget,
  sanitizeFrontendValues,
  setBackendInvalidMessage,
} from '@/views/selfservice/helper';
import _ from '@/jsHelper/translate';
import MyForm from '@/components/forms/Form.vue';
import { validateAll, initialValue, isValid, allValid, WidgetDefinition } from '@/jsHelper/forms';
import Site from '@/views/selfservice/Site.vue';
import ErrorDialog from '@/views/selfservice/ErrorDialog.vue';
import ConfirmDeregistration from '@/views/selfservice/ConfirmDeregistration.vue';
import activity from '@/jsHelper/activity';

interface Data {
  initiated: boolean,
  forceLogin: boolean,
  loginWidgets: WidgetDefinition[],
  loginValues: Record<string, string>,
  attributeWidgets: WidgetDefinition[],
  attributeValues: Record<string, unknown>,
  origFormValues: Record<string, unknown>,
}

export default defineComponent({
  name: 'Profile',
  components: {
    MyForm,
    Site,
    ErrorDialog,
    ConfirmDeregistration,
  },
  data(): Data {
    // TODO translations
    return {
      loginWidgets: [{
        type: 'TextBox',
        name: 'username',
        label: _('Username'),
        invalidMessage: '',
        required: true,
      }, {
        type: 'PasswordBox',
        name: 'password',
        label: _('Password'),
        invalidMessage: '',
        required: true,
      }],
      loginValues: {
        username: '',
        password: '',
      },
      attributeWidgets: [],
      attributeValues: {},
      origFormValues: {},
      initiated: false,
      forceLogin: false,
    };
  },
  computed: {
    ...mapGetters({
      userState: 'user/userState',
      activityLevel: 'activity/level',
      metaData: 'metaData/getMeta',
      initialLoadDone: 'getInitialLoadDone',
    }),
    renderDeregistration(): boolean {
      return isTrue(this.metaData['umc/self-service/account-deregistration/enabled'] ?? false);
    },
    TITLE(): string {
      return _('Profile');
    },
    SUBTITLE(): string {
      return _('Customize your profile');
    },
    USERNAME(): string {
      return _('Username');
    },
    PASSWORD(): string {
      return _('Password');
    },
    CONTINUE(): string {
      return _('Continue');
    },
    CLOSE(): string {
      return _('Close');
    },
    SAVE(): string {
      return _('Save');
    },
    DELETE_ACCOUNT(): string {
      return _('Delete my account');
    },
    attributesLoaded(): boolean {
      return this.attributeWidgets.length > 0;
    },
    loginForm(): typeof MyForm {
      return this.$refs.loginForm as typeof MyForm;
    },
    attributesForm(): typeof MyForm {
      return this.$refs.attributesForm as typeof MyForm;
    },
    errorDialog(): typeof ErrorDialog {
      return this.$refs.errorDialog as typeof ErrorDialog;
    },
    confirmDeregistrationDialog(): typeof ConfirmDeregistration {
      return this.$refs.confirmDeregistrationDialog as typeof ConfirmDeregistration;
    },
    tabindex(): number {
      return activity(['selfservice'], this.activityLevel);
    },
    skipLogin(): boolean {
      return !this.forceLogin && this.userState.username && this.metaData['umc/self-service/allow-authenticated-use'];
    },
    loginWidgetsVisible(): WidgetDefinition[] {
      if (this.skipLogin) {
        return [this.loginWidgets[0]];
      }
      return this.loginWidgets;
    },
    loginWidgetsWithTabindex(): WidgetDefinition[] {
      return this.loginWidgetsVisible.map((widget) => {
        widget.tabindex = this.tabindex;
        return widget;
      });
    },
    attributeWidgetsWithTabindex(): WidgetDefinition[] {
      return this.attributeWidgets.map((widget) => {
        widget.tabindex = this.tabindex;
        return widget;
      });
    },
    credentials(): { username?: string, password?: string } {
      if (this.skipLogin) {
        return {};
      }
      return {
        username: this.loginValues.username,
        password: this.loginValues.password,
      };
    },
  },
  watch: {
    initialLoadDone(loadDone) {
      if (loadDone && !this.initiated) {
        this.init();
      }
    },
  },
  mounted() {
    if (this.initialLoadDone) {
      this.init();
    }
  },
  methods: {
    init() {
      this.initiated = true;
      if (this.userState?.username) {
        this.loginValues.username = this.userState.username ? this.userState.username : null;
        this.loginWidgets[0].disabled = true;
      }

      if (this.skipLogin) {
        this.onContinue();
      } else {
        // FIXME (would like to get rid of setTimeout)
        // when this site is opening via a SideNavigation.vue entry then
        // 'activity/setRegion', 'portal-header' is called when SideNavigation is closed
        // which calls focusElement which uses setTimeout, 50
        // so we have to also use setTimeout
        setTimeout(() => {
          this.loginForm.focusFirstInteractable();
        }, 100);
      }
    },
    onContinue() {
      if (!this.skipLogin) {
        validateAll(this.loginWidgets, this.loginValues);
        if (!allValid(this.loginWidgets)) {
          this.loginForm.focusFirstInvalid();
          return;
        }
      }
      this.loginWidgets.forEach((widget) => {
        widget.disabled = true;
      });
      this.loadAttributes();
    },
    resetToLogin() {
      this.forceLogin = true;
      this.attributeWidgets = [];
      this.attributeValues = {};
      this.loginWidgets.forEach((widget) => {
        widget.disabled = false;
      });
      this.loginValues = {
        username: '',
        password: '',
      };
      this.$nextTick(() => {
        this.loginForm.focusFirstInteractable();
      });
    },
    close() {
      this.$router.push({ name: 'portal' });
    },
    onSave() {
      validateAll(this.attributeWidgets, this.attributeValues);
      if (!allValid(this.attributeWidgets)) {
        return;
      }

      const alteredValues = Object.keys(this.attributeValues).reduce((_alteredValues, attributeName) => {
        if (!isEqual(this.attributeValues[attributeName], this.origFormValues[attributeName])) {
          _alteredValues[attributeName] = this.attributeValues[attributeName];
        }
        return _alteredValues;
      }, {});

      if (isEmpty(alteredValues)) {
        this.$store.dispatch('notifications/addSuccessNotification', {
          title: _('Profile changes'),
          description: 'Your profile data is up to date',
        });
        return;
      }
      this.save(sanitizeFrontendValues(alteredValues, this.attributeWidgets));
    },
    save(values) {
      this.$store.dispatch('activateLoadingState');
      umcCommand('passwordreset/validate_user_attributes', {
        attributes: values,
        ...this.credentials,
      })
        .then((result) => {
          setBackendInvalidMessage(this.attributeWidgets, result);
          if (!allValid(this.attributeWidgets)) {
            this.attributesForm.focusFirstInvalid();
            return undefined;
          }
          return umcCommand('passwordreset/set_user_attributes', {
            attributes: values,
            ...this.credentials,
          }).then(() => {
            this.$store.dispatch('notifications/addSuccessNotification', {
              title: _('Profile changes'),
              description: 'Successfully saved changes',
            });
            this.updateOrigFormValues();
          });
        })
        .catch((error) => {
          this.errorDialog.showError(error.message)
            .then(() => {
              (this.$refs.saveButton as HTMLButtonElement).focus();
            });
        })
        .finally(() => {
          this.$store.dispatch('deactivateLoadingState');
        });
    },
    updateOrigFormValues() {
      this.origFormValues = JSON.parse(JSON.stringify(this.attributeValues));
    },
    loadAttributes() {
      this.$store.dispatch('activateLoadingState');
      umcCommand('passwordreset/get_user_attributes_descriptions', {})
        .then((widgets) => {
          const attributes = widgets.map((widget) => widget.id);
          return umcCommand('passwordreset/get_user_attributes_values', {
            attributes,
            ...this.credentials,
          }).then((values) => {
            const sanitized = widgets.map((widget) => sanitizeBackendWidget(widget));
            sanitized.forEach((widget) => {
              values[widget.name] = initialValue(widget, values[widget.name]);
            });
            this.attributeWidgets = sanitized;
            this.attributeValues = sanitizeBackendValues(values, sanitized);
            this.updateOrigFormValues();
            this.$nextTick(() => {
              this.attributesForm.focusFirstInteractable();
            });
          });
        })
        .catch((error) => {
          this.errorDialog.showError(error.message)
            .then(() => {
              this.resetToLogin();
            });
        })
        .finally(() => {
          this.$store.dispatch('deactivateLoadingState');
        });
    },
    deleteAccount(): void {
      this.confirmDeregistrationDialog.show(this.skipLogin)
        .then((password) => {
          umcCommandWithStandby(this.$store, 'passwordreset/deregister_account', {
            username: this.loginValues.username,
            password: this.skipLogin ? password : this.loginValues.password,
          })
            .then(() => {
              this.errorDialog.showError(_('Your account has been successfully deleted.'), _('Account deletion'), 'dialog')
                .then(() => {
                  this.resetToLogin();
                });
            }, (err) => {
              this.errorDialog.showError(err.message)
                .then(() => {
                  (this.$refs.deregistrationButton as HTMLButtonElement).focus();
                });
            });
        });
    },
  },
});
</script>
