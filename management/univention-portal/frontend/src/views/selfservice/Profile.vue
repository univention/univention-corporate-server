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
    :ucr-var-for-frontend-enabling="'umc/self-service/profiledata/enabled'"
  >
    <my-form
      ref="loginForm"
      v-model="loginValues"
      :widgets="loginWidgets"
    >
      <footer v-if="!attributesLoaded">
        <button
          type="submit"
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
      :widgets="attributeWidgets"
    >
      <footer>
        <button
          type="button"
          @click="onCancel"
        >
          {{ CANCEL }}
        </button>
        <button
          ref="saveButton"
          type="submit"
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
  </site>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

import isEmpty from 'lodash.isempty';
import isEqual from 'lodash.isequal';
import { umc, umcCommand } from '@/jsHelper/umc';
import _ from '@/jsHelper/translate';
import MyForm from '@/components/forms/Form.vue';
import { validateAll, initialValue, isValid, allValid } from '@/jsHelper/forms';
import Site from '@/views/selfservice/Site.vue';
import ErrorDialog from '@/views/selfservice/ErrorDialog.vue';

interface Data {
  loginWidgets: any[],
  loginValues: any,
  attributeWidgets: any[],
  attributeValues: any,
  origFormValues: any,
  showModal: boolean,
}

export default defineComponent({
  name: 'Profile',
  components: {
    MyForm,
    Site,
    ErrorDialog,
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
      showModal: false,
    };
  },
  computed: {
    ...mapGetters({
      userState: 'user/userState',
    }),
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
    CANCEL(): string {
      return _('Cancel');
    },
    SAVE(): string {
      return _('Save');
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
  },
  mounted() {
    this.showModal = true;
    if (this.userState?.username) {
      this.loginValues.username = this.userState.username ? this.userState.username : null;
      this.loginWidgets[0].disabled = true;
    }
    this.loginForm.focusFirstInteractable();
  },
  methods: {
    onContinue() {
      validateAll(this.loginWidgets, this.loginValues);
      if (!allValid(this.loginWidgets)) {
        this.loginForm.focusFirstInvalid();
        return;
      }
      this.loginWidgets.forEach((widget) => {
        widget.disabled = true;
      });
      this.loadAttributes();
    },
    onCancel() {
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
      this.save(alteredValues);
    },
    save(values) {
      this.$store.dispatch('activateLoadingState');
      umcCommand('passwordreset/validate_user_attributes', {
        username: this.loginValues.username,
        password: this.loginValues.password,
        attributes: values,
      })
        .then((result) => {
          this.attributeWidgets.forEach((widget) => {
            const validationObj = result[widget.name];
            if (validationObj !== undefined) {
              switch (widget.type) {
                case 'TextBox':
                case 'DateBox':
                case 'ComboBox':
                case 'PasswordBox':
                  widget.invalidMessage = validationObj.message;
                  break;
                case 'MultiInput':
                  // TODO test if non array can come from backend
                  if (Array.isArray(validationObj.message)) {
                    widget.invalidMessage = {
                      all: '',
                      values: validationObj.message,
                    };
                  } else {
                    widget.invalidMessage = {
                      all: validationObj.message,
                      values: [],
                    };
                  }
                  break;
                default:
                  break;
              }
            }
          });
          if (!allValid(this.attributeWidgets)) {
            this.attributesForm.focusFirstInvalid();
            return;
          }
          umcCommand('passwordreset/set_user_attributes', {
            username: this.loginValues.username,
            password: this.loginValues.password,
            attributes: values,
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
            username: this.loginValues.username,
            password: this.loginValues.password,
            attributes,
          }).then((values) => {
            const sanitizeWidget = (widget) => {
              const w: any = {
                // TODO unhandled fields that come from command/passwordreset/get_user_attributes_descriptions
                // description: ""
                // multivalue: false
                // size: "TwoThirds"
                // syntax: "TwoThirdsString"
                type: widget.type,
                name: widget.id ?? '',
                label: widget.label ?? '',
                required: widget.required ?? false,
                readonly: !(widget.editable ?? true) || (widget.readonly ?? false),
              };
              if (widget.type === 'ComboBox') {
                w.options = widget.staticValues;
              }
              if (widget.type === 'MultiInput') {
                w.extraLabel = w.label;
                w.subtypes = widget.subtypes.map((subtype) => sanitizeWidget(subtype));
              }
              return w;
            };
            const sanitized = widgets.map((widget) => sanitizeWidget(widget));
            sanitized.forEach((widget) => {
              values[widget.name] = initialValue(widget, values[widget.name]);
            });
            this.attributeWidgets = sanitized;
            this.attributeValues = values;
            this.updateOrigFormValues();
            this.$nextTick(() => {
              this.attributesForm.focusFirstInteractable();
            });
          });
        })
        .catch((error) => {
          this.errorDialog.showError(error.message)
            .then(() => {
              this.onCancel();
            });
        })
        .finally(() => {
          this.$store.dispatch('deactivateLoadingState');
        });
    },
  },
});
</script>
