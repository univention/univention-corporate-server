<template>
  <modal-dialog
    :i18n-title-key="label"
    @cancel="cancel"
  >
    <form
      @submit.prevent="finish"
    >
      <main>
        <label>
          <translate i18n-key="NAME" />
          <input
            ref="input"
            type="text"
            :list="datalistId"
            name="display_name"
          >
          <datalist
            :id="datalistId"
          >
            <option
              v-for="item in items"
              :key="item.dn"
              :value="$localized(item.name)"
              :data-value="item.dn"
            />
          </datalist>
        </label>
      </main>
      <footer>
        <button
          type="button"
          @click.prevent="cancel"
        >
          <translate i18n-key="CANCEL" />
        </button>
        <button
          type="submit"
          @click.prevent="finish"
        >
          <translate i18n-key="ADD" />
        </button>
      </footer>
    </form>
  </modal-dialog>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

import ModalDialog from '@/components/ModalDialog.vue';
import Translate from '@/i18n/Translate.vue';

import { setInvalidity } from '@/jsHelper/tools';
import { udmPut } from '@/jsHelper/umc';

interface ExistingEntryData {
  datalistId: string,
}

export default defineComponent({
  name: 'ExistingEntry',
  components: {
    ModalDialog,
    Translate,
  },
  props: {
    label: {
      type: String,
      required: true,
    },
    categoryDn: {
      type: String,
      required: true,
    },
    objectGetter: {
      type: String,
      required: true,
    },
  },
  data(): ExistingEntryData {
    return {
      datalistId: Math.random()
        .toString(36)
        .substr(2, 4),
    };
  },
  computed: {
    ...mapGetters({
      portalCategories: 'portalData/portalCategories',
    }),
    items(): any[] {
      return this.$store.getters[this.objectGetter];
    },
  },
  methods: {
    cancel() {
      this.$store.dispatch('modal/hideAndClearModal');
    },
    async finish() {
      const input = this.$refs.input as HTMLFormElement;
      const list = input.getAttribute('list');
      const options = document.querySelectorAll(`#${list} option`);

      let dn: string | null = null;
      for (let k = 0; k < options.length; k += 1) {
        const option = options[k];

        if (option.getAttribute('value') === input.value) {
          dn = option.getAttribute('data-value');
          break;
        }
      }
      setInvalidity(this, 'input', !dn);
      if (dn) {
        const category = this.portalCategories.find((cat) => cat.dn === this.categoryDn);
        const categoryAttrs = {
          entries: category.entries.concat([dn]),
        };
        console.info('Adding', dn, 'to', this.categoryDn);
        try {
          await udmPut(this.categoryDn, categoryAttrs);
          this.$store.dispatch('notificationBubble/addSuccessNotification', {
            bubbleTitle: this.$translateLabel('ENTRY_ADDED_SUCCESS'),
          });
        } catch (err) {
          console.error(err.message);
          this.$store.dispatch('notificationBubble/addErrorNotification', {
            bubbleTitle: this.$translateLabel('ENTRY_ADDED_FAILURE'),
          });
        }
        this.$store.dispatch('modal/hideAndClearModal');
      }
    },
  },
});
</script>
