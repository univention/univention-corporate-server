<template>
  <modal-wrapper
    :is-active="isActive"
    :full="true"
    class="modal-wrapper--selfservice"
  >
    <modal-dialog
      v-if="isActive"
      ref="dialog"
      :i18n-title-key="title"
      class="dialog--selfservice"
      @cancel="cancel"
      @keydown.tab="onTab"
    >
      <p
        v-for="(error, idx) in errors"
        :key="idx"
      >
        {{ error }}
      </p>
      <form>
        <footer>
          <button
            ref="button"
            type="button"
            @click="cancel"
          >
            {{ CLOSE }}
          </button>
        </footer>
      </form>
    </modal-dialog>
  </modal-wrapper>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import ModalDialog from '@/components/modal/ModalDialog.vue';
import ModalWrapper from '@/components/modal/ModalWrapper.vue';
import _ from '@/jsHelper/translate';

interface Data {
  errors: string[],
  givenTitle: string,
  promiseResolve: null,
}

export default defineComponent({
  name: 'ConfirmDialog',
  components: {
    ModalDialog,
    ModalWrapper,
  },
  data(): Data {
    return {
      errors: [],
      givenTitle: '',
      promiseResolve: null, // TODO | Promise resolve callback
    };
  },
  computed: {
    isActive(): boolean {
      return this.errors.length > 0;
    },
    title(): string {
      return this.givenTitle || _('An error occurred');
    },
    CLOSE(): string {
      return _('Close');
    },
  },
  methods: {
    cancel(): void {
      this.errors = [];
      this.givenTitle = '';
      // @ts-ignore TODO
      this.promiseResolve();
    },
    showError(message: string | string[], title = ''): Promise<undefined> {
      this.givenTitle = title;
      if (Array.isArray(message)) {
        this.errors = [];
        message.forEach((error) => {
          this.errors.push(error);
        });
      } else {
        this.errors = [message];
      }
      // @ts-ignore
      this.$nextTick(() => {
        (this.$refs.button as HTMLButtonElement).focus();
      });
      return new Promise((resolve, reject) => {
        // @ts-ignore TODO
        this.promiseResolve = resolve;
      });
    },
    onTab(evt): void {
      const els = (this.$refs.dialog as typeof ModalDialog).$el.querySelectorAll('button:not([tabindex="-1"]), [href]:not([tabindex="-1"]), input:not([tabindex="-1"]), select:not([tabindex="-1"]), textarea:not([tabindex="-1"]), [tabindex]:not([tabindex="-1"])');
      const firstEl = els[0];
      const lastEl = els[els.length - 1];
      if (document.activeElement === firstEl && evt.shiftKey) {
        evt.preventDefault();
        lastEl.focus();
        return;
      }
      if (document.activeElement === lastEl && !evt.shiftKey) {
        evt.preventDefault();
        firstEl.focus();
      }
    },
  },
});
</script>
