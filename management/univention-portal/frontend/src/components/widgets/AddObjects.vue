<!--
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
-->
<template>
  <modal-dialog
    :i18n-title-key="ADD_OBJECTS"
    @cancel="cancel"
  >
    <form
      @submit.prevent="search"
    >
      <label>
        {{ SEARCH }}
        <div class="add-objects__search-wrapper">
          <input
            ref="search"
            v-model="searchString"
            name="search"
            class="add-objects__text-input"
          >
          <icon-button
            icon="search"
            :active-at="['modal2']"
            :aria-label-prop="SEARCH"
            :has-button-style="true"
            @click="search"
          />
        </div>
      </label>
      <label>{{ RESULTS }}</label>
      <div
        class="multi-select__select"
      >
        <label
          v-for="value in available"
          :key="value"
        >
          <input
            type="checkbox"
            @change="toggleSelection(value)"
          >
          <span>{{ dnToLabel(value) }}</span>
        </label>
      </div>
      <footer>
        <button
          type="button"
          @click.prevent="cancel"
        >
          <portal-icon
            icon="x"
          />
          <span>{{ CANCEL }}</span>
        </button>
        <button
          type="button"
          @click.prevent="finish"
        >
          <portal-icon
            icon="check"
          />
          <span>{{ ADD }}</span>
        </button>
      </footer>
    </form>
  </modal-dialog>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';
import _ from '@/jsHelper/translate';
import { udmChoices, Choice } from '@/jsHelper/umc';

import PortalIcon from '@/components/globals/PortalIcon.vue';
import ModalDialog from '@/components/modal/ModalDialog.vue';
import IconButton from '@/components/globals/IconButton.vue';

interface AddObjectsData {
  searchString: string,
  available: string[],
  selection: string[],
}

export default defineComponent({
  name: 'AddObjects',
  components: {
    IconButton,
    ModalDialog,
    PortalIcon,
  },
  props: {
    alreadyAdded: {
      type: Array as PropType<string[]>,
      required: true,
    },
  },
  data(): AddObjectsData {
    return {
      searchString: '',
      available: [],
      selection: [],
    };
  },
  computed: {
    RESULTS(): string {
      return _('%(num)s result(s)', { num: this.available.length.toString() });
    },
    SEARCH(): string {
      return _('Search');
    },
    ADD_OBJECTS(): string {
      return _('Add groups');
    },
    CANCEL(): string {
      return _('Cancel');
    },
    ADD(): string {
      return _('Add');
    },
  },
  async mounted() {
    await this.search();
    (this.$refs.search as HTMLElement).focus();
  },
  methods: {
    toggleSelection(value: string) {
      const idx = this.selection.indexOf(value);
      if (idx > -1) {
        this.selection.splice(idx, 1);
      } else {
        this.selection.push(value);
      }
    },
    async search() {
      this.$store.dispatch('activateLoadingState');
      let result: Choice[] = [];
      try {
        const response = await udmChoices('groups/group', 'GroupDN', this.searchString);
        result = response.data.result;
      } catch (err) {
        console.warn(err);
      }
      this.available = result
        .filter((group) => !this.alreadyAdded.includes(group.id))
        .map((group) => group.id);
      this.$store.dispatch('deactivateLoadingState');
    },
    finish() {
      this.$store.dispatch('modal/resolve', {
        level: 2,
        selection: this.selection,
      });
    },
    dnToLabel(dn: string): string {
      const idx = dn.indexOf(',');
      return dn.slice(3, idx);
    },
    cancel() {
      this.$store.dispatch('modal/resolve', {
        level: 2,
        selection: [],
      });
    },
  },
});
</script>

<style lang="stylus">
.add-objects
  &__search-wrapper
    display: flex
    align-items: center
  &__text-input
    margin-right: var(--layout-spacing-unit)
    margin-bottom: 0
</style>
