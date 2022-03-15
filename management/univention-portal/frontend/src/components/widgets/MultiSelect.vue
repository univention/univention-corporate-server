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
  <div class="multi-select">
    <fieldset>
      <div
        class="multi-select__select"
      >
        <label
          v-for="value in modelValue"
          :key="value"
        >
          <input
            :ref="`checkbox-${value}`"
            type="checkbox"
            :tabindex="tabindex"
            @change="toggleSelection(value)"
          >
          <span data-test="multi-select-checkbox-span">{{ dnToLabel(value) }}</span>
        </label>
      </div>
      <footer class="multi-select__footer">
        <button
          id="multi-select-add-more-button"
          ref="addButton"
          type="button"
          :tabindex="tabindex"
          data-test="multi-select-add-more-button"
          @click.prevent="add"
        >
          <portal-icon
            icon="plus"
          />
          <span aria-hidden="true">
            {{ ADD_MORE }}
          </span>
          <span class="sr-only sr-only-mobile">
            {{ ADD_GROUPS }}
          </span>
        </button>
        <button
          type="button"
          :disabled="!elementsSelected || modelValue.length === 0"
          :tabindex="tabindex"
          data-test="multi-select-remove-button"
          @click.prevent="remove"
        >
          <portal-icon
            icon="trash"
          />
          <span aria-hidden="true">
            {{ REMOVE }}
          </span>
          <span class="sr-only sr-only-mobile">
            {{ REMOVE_SELECTION }}
          </span>
        </button>
      </footer>
    </fieldset>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';
import _ from '@/jsHelper/translate';

import PortalIcon from '@/components/globals/PortalIcon.vue';

interface MultiSelectSelection {
  selection: string[],
}

export default defineComponent({
  name: 'MultiSelect',
  components: {
    PortalIcon,
  },
  props: {
    modelValue: {
      type: Array as PropType<string[]>,
      required: true,
    },
    name: {
      type: String,
      required: true,
    },
    tabindex: {
      type: Number,
      default: 0,
    },
  },
  emits: ['update:modelValue'],
  data(): MultiSelectSelection {
    return {
      selection: [],
    };
  },
  computed: {
    ADD_MORE(): string {
      return _('Add more');
    },
    ADD_GROUPS(): string {
      return _('Add Groups');
    },
    REMOVE(): string {
      return _('Remove');
    },
    REMOVE_SELECTION(): string {
      return ` ${_('Remove selection')}`;
    },
    elementsSelected(): boolean {
      return this.selection.length > 0;
    },
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
    dnToLabel(dn: string): string {
      const idx = dn.indexOf(',');
      return dn.slice(3, idx);
    },
    add() {
      this.$store.dispatch('modal/setShowModalPromise', {
        level: 2,
        name: 'AddObjects',
        props: {
          alreadyAdded: this.modelValue,
        },
        stubborn: true,
      }).then((values) => {
        this.$store.dispatch('modal/hideAndClearModal', 2);
        const newValues = this.modelValue.concat(values.selection);
        newValues.sort();
        this.$emit('update:modelValue', newValues);
        this.$store.dispatch('activity/setMessage', _('Added to selection'));
        this.$store.dispatch('activity/setRegion', 'modal-wrapper--isVisible-1');
      });
      this.$store.dispatch('activity/setLevel', 'modal2');
      this.$store.dispatch('activity/saveFocus', {
        region: 'modal-wrapper--isVisible-1',
        id: 'multi-select-add-more-button',
      });
    },
    remove() {
      const values = this.modelValue.filter((value) => !this.selection.includes(value));
      this.$emit('update:modelValue', values);
      this.$store.dispatch('activity/setMessage', _('Removed selection'));
    },
    focus() {
      if (this.modelValue.length > 0) {
        const name = this.modelValue[0];
        // @ts-ignore TODO
        this.$refs[`checkbox-${name}`].focus();
      } else {
        // @ts-ignore TODO
        this.$refs.addButton.focus();
      }
    },
  },
});
</script>

<style lang="stylus">
.multi-select
  &__select
    padding: 0 var(--layout-spacing-unit)
    background-color: var(--bgc-inputfield-on-container)
    border: 0.1rem solid var(--bgc-inputfield-on-container)
    border-radius: var(--border-radius-interactable)
    height: calc(5 * var(--inputfield-size))
    overflow: auto

    label
      margin-top: var(--layout-spacing-unit) !important
      display: flex

      input
        flex-shrink: 0

      span
        overflow: hidden
        text-overflow: ellipsis

  &__footer
    margin: var(--layout-spacing-unit) 0
    display: flex
    button + button
      margin-left: var(--layout-spacing-unit)
</style>
