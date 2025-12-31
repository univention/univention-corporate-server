<!--
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
-->
<template>
  <site
    :title="title"
    :subtitle="subtitle"
  >
    <my-form
      :id="id"
      ref="form"
      v-model="formValues"
      :widgets="formWidgetsWithTabindex"
    >
      <slot />
      <footer>
        <button
          type="submit"
          :tabindex="tabindex"
          :class="{'button--primary' : loaded}"
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
import activity from '@/jsHelper/activity';

interface FormData {
  username: string,
  password?: string,
}

interface Data {
  formValues: FormData,
  formWidgets: WidgetDefinition[],
  loaded: boolean,
}

export default defineComponent({
  name: 'GuardedSite',
  components: {
    MyForm,
    Site,
    ErrorDialog,
  },
  props: {
    id: {
      type: String,
      required: false,
    },
    title: {
      type: String,
      required: true,
    },
    subtitle: {
      type: String,
      default: '',
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
    };
  },
  computed: {
    ...mapGetters({
      userState: 'user/userState',
      activityLevel: 'activity/level',
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
    tabindex(): number {
      return activity(['selfservice'], this.activityLevel);
    },
    formWidgetsTranslated(): WidgetDefinition[] {
      return this.formWidgets.map((widget) => {
        switch (widget.name) {
          case 'username':
            widget.label = _('Username');
            break;
          case 'password':
            widget.label = _('Password');
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
      } else if (this.userState.username) {
        this.formValues.username = this.userState.username;
      }
      this.refocus();
    }, 300); // TODO...
  },
  methods: {
    refocus() {
      // @ts-ignore TODO
      this.$nextTick(() => {
        this.form.focusFirstInteractable();
      });
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
          this.disableLoginWidgets(true);
          this.loaded = true;
          this.$emit('loaded', result, this.formValues);
          this.refocus();
        })
        .catch((error) => {
          this.disableLoginWidgets(false);
          this.formValues.username = '';
          if (this.passwordNeeded) {
            this.formValues.password = '';
          }
          this.showError(error.message, _('Authentification failed'))
            .then(() => {
              this.refocus();
            });
        });
    },
    showError(message: string | string[], title = ''): Promise<undefined> {
      return (this.$refs.errorDialog as typeof ErrorDialog).showError(message, title);
    },
    disableLoginWidgets(disabled: boolean): void {
      ['username', 'password'].forEach((attrName) => {
        const widget = this.formWidgets.find((w) => w.name === attrName);
        if (widget) {
          widget.disabled = disabled;
        }
      });
    },
  },
});
</script>
