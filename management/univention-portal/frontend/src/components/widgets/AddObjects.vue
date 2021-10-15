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
          {{ CANCEL }}
        </button>
        <button
          type="button"
          @click.prevent="finish"
        >
          <portal-icon
            icon="check"
          />
          {{ ADD }}
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
