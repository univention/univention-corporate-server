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
    :title="title"
    :subtitle="subtitle"
    :ucr-var-for-frontend-enabling="ucrVarForFrontendEnabling"
  >
    <my-form
      ref="form"
      v-model="formValues"
      :widgets="formWidgets"
    >
      <slot />
      <footer>
        <button
          type="submit"
          :class="{'primary' : loaded}"
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
import { defineComponent, PropType } from 'vue';

import { umcCommandWithStandby } from '@/jsHelper/umc';
import Site from '@/views/selfservice/Site.vue';
import MyForm from '@/components/forms/Form.vue';
import { WidgetDefinition, validateAll } from '@/jsHelper/forms';
import { mapGetters } from 'vuex';
import _ from '@/jsHelper/translate';
import ErrorDialog from '@/views/selfservice/ErrorDialog.vue';

interface FormData {
  username: string,
  password?: string,
}

interface Data {
  formValues: FormData,
  formWidgets: WidgetDefinition[],
  loaded: boolean,
  usernameGiven: boolean,
}

export default defineComponent({
  name: 'GuardedSite',
  components: {
    MyForm,
    Site,
    ErrorDialog,
  },
  props: {
    title: {
      type: String,
      required: true,
    },
    subtitle: {
      type: String,
      required: true,
    },
    path: {
      type: String,
      required: true,
    },
    passwordNeeded: {
      type: Boolean,
      default: true,
    },
    guardedWidgets: {
      type: Array as PropType<WidgetDefinition[]>,
      required: true,
    },
    ucrVarForFrontendEnabling: {
      type: String,
      default: '',
    },
    submitLabelAfterLoaded: {
      type: String,
      default: '',
    },
  },
  emits: ['loaded', 'save'],
  data(): Data {
    const formValues: FormData = {
      username: '',
    };
    if (this.passwordNeeded) {
      formValues.password = '';
    }
    const formWidgets: WidgetDefinition[] = [{
      type: 'TextBox',
      name: 'username',
      label: _('Username'),
      readonly: false, // TODO
      invalidMessage: '',
      required: true,
    }];
    if (this.passwordNeeded) {
      formWidgets.push({
        type: 'PasswordBox',
        name: 'password',
        label: _('Password'),
        readonly: false,
        invalidMessage: '',
        required: true,
      });
    }
    return {
      formValues,
      formWidgets,
      loaded: false,
      usernameGiven: false,
    };
  },
  computed: {
    ...mapGetters({
      metaData: 'metaData/getMeta',
      userState: 'user/userState',
    }),
    SUBMIT_LABEL(): string {
      if (this.loaded) {
        return this.submitLabelAfterLoaded || _('Submit');
      }
      return _('Next');
    },
    form(): typeof MyForm {
      return this.$refs.form as typeof MyForm;
    },
  },
  watch: {
    guardedWidgets(newValue) {
      newValue.forEach((widget) => {
        this.formWidgets.push({ ...widget });
      });
    },
  },
  mounted() {
    setTimeout(() => {
      if (typeof this.$route.query.username === 'string' && this.$route.query.username) {
        this.formValues.username = this.$route.query.username;
        this.usernameGiven = true;
      } else if (this.userState.username) {
        this.formValues.username = this.userState.username;
        this.usernameGiven = true;
      }
      this.refocus();
    }, 300); // TODO...
  },
  methods: {
    refocus() {
      this.form.focusFirstInteractable();
    },
    submit() {
      if (!validateAll(this.formWidgets, this.formValues)) {
        this.form.focusFirstInvalid();
        return;
      }
      if (this.loaded) {
        this.$emit('save', this.formValues);
        return;
      }
      const params: FormData = {
        username: this.formValues.username,
      };
      if (this.passwordNeeded) {
        params.password = this.formValues.password;
      }
      umcCommandWithStandby(this.$store, this.path, params)
        .then((result) => {
          this.loaded = true;
          this.$emit('loaded', result, this.formValues);
          this.refocus();
        })
        .catch((error) => {
          this.formValues.username = '';
          if (this.passwordNeeded) {
            this.formValues.password = '';
          }
          this.usernameGiven = false;
          this.showError(error.message, _('Authentification failed'))
            .then(() => {
              this.refocus();
            });
        });
    },
    showError(message: string | string[], title = ''): Promise<undefined> {
      return (this.$refs.errorDialog as typeof ErrorDialog).showError(message, title);
    },
  },
});
</script>
