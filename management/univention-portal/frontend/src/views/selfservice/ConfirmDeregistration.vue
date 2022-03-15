<template>
  <modal-wrapper
    :is-active="isActive"
    :full="true"
    class="modal-wrapper--selfservice"
  >
    <modal-dialog
      v-if="isActive"
      ref="dialog"
      modal-level="selfservice2"
      :i18n-title-key="TITLE"
      class="dialog--selfservice"
      @cancel="cancel"
    >
      <template #description>
        {{ DESCRIPTION }}
      </template>
      <my-form
        ref="form"
        v-model="formValues"
        :widgets="visibleWidgets"
      >
        <footer>
          <button
            ref="cancelButon"
            type="button"
            @click="cancel"
          >
            {{ CANCEL }}
          </button>
          <button
            ref="confirmButton"
            type="submit"
            @click.prevent="confirm"
          >
            {{ CONFIRM }}
          </button>
        </footer>
      </my-form>
    </modal-dialog>
  </modal-wrapper>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import ModalDialog from '@/components/modal/ModalDialog.vue';
import ModalWrapper from '@/components/modal/ModalWrapper.vue';
import MyForm from '@/components/forms/Form.vue';
import _ from '@/jsHelper/translate';
import { allValid, isEmpty, validateAll, WidgetDefinition } from '@/jsHelper/forms';

interface Data {
  isActive: boolean,
  showPasswordPrompt: boolean,
  promiseResolve: null,
  formValues: {
    password: string,
  },
  formWidgets: WidgetDefinition[],
}

export default defineComponent({
  name: 'ConfirmDialog',
  components: {
    ModalDialog,
    ModalWrapper,
    MyForm,
  },
  data(): Data {
    return {
      isActive: false,
      showPasswordPrompt: true,
      promiseResolve: null, // TODO | Promise resolve callback
      formValues: {
        password: '',
      },
      formWidgets: [{
        type: 'PasswordBox',
        name: 'password',
        label: _('Password'),
        validators: [(widget, value) => (
          isEmpty(widget, value) ? _('Please enter your password') : ''
        )],
      }],
    };
  },
  computed: {
    TITLE(): string {
      return _('Account deletion');
    },
    DESCRIPTION(): string {
      if (this.showPasswordPrompt) {
        return _('Please enter your password to delete your account');
      }
      return _('Do you really want to delete your account?');
    },
    CANCEL(): string {
      return _('Cancel');
    },
    CONFIRM(): string {
      return _('Delete my account');
    },
    visibleWidgets(): WidgetDefinition[] {
      if (this.showPasswordPrompt) {
        return this.formWidgets;
      }
      return [];
    },
  },
  methods: {
    cancel(): void {
      this.isActive = false;
      this.$store.dispatch('activity/setLevel', 'selfservice');
    },
    confirm(): void {
      if (this.showPasswordPrompt) {
        validateAll(this.formWidgets, this.formValues);
        if (!allValid(this.formWidgets)) {
          (this.$refs.form as typeof MyForm).focusFirstInvalid();
          return;
        }
      }
      this.cancel();
      // @ts-ignore
      this.promiseResolve(this.formValues.password);
    },
    show(loginSkipped: boolean): Promise<string> {
      this.formValues = {
        password: '',
      };
      this.showPasswordPrompt = loginSkipped;
      this.isActive = true;
      this.$store.dispatch('activity/setLevel', 'selfservice2');
      if (this.showPasswordPrompt) {
        // @ts-ignore
        this.$nextTick(() => {
          (this.$refs.form as typeof MyForm).focusFirstInteractable();
        });
      } else {
        // @ts-ignore
        this.$nextTick(() => {
          (this.$refs.cancelButon as HTMLButtonElement).focus();
        });
      }
      return new Promise((resolve, reject) => {
        // @ts-ignore TODO
        this.promiseResolve = resolve;
      });
    },
  },
});
</script>
