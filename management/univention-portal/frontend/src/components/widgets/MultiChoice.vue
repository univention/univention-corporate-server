<!--
  Copyright 2021-2024 Univention GmbH
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
  <div
    class="multi-choice"
    tabindex="0"
  >
    <select
      :id="forAttrOfLabel"
      :name="name"
      aria-hidden="true"
      :aria-invalid="invalid"
      :aria-describedby="invalidMessageId || null"
      multiple
      class="multi-choice-select"
    >
      <option
        v-for="(item, index) in lists"
        :key="index"
        :value="getItemName(item)"
        :selected="isItemChecked(item)"
      >
        {{ getItemName(item) }}
      </option>
    </select>
    <div class="multi-choice-checkboxes">
      <div
        v-for="(item, index) in lists"
        :key="index"
        ref="checkboxEls"
        class="multi-choice-checkboxes__checkbox"
        tabindex="-1"
      >
        <div
          :id="`multi-choice-checkboxes__checkbox--${index}`"
          role="checkbox"
          :aria-checked="isItemChecked(item)"
          :aria-label="getItemName(item)"
          :aria-labelledby="`multi-choice-checkboxes__checkbox--${index}-label`"
          aria-disabled="false"
          tabindex="-1"
          @click="onCheck(item)"
        />
        <label
          :id="`multi-choice-checkboxes__checkbox--${index}-label`"
          :for="`multi-choice-checkboxes__checkbox--${index}`"
          tabindex="-1"
          @click="onCheck(item)"
        >
          {{ getItemName(item) }}
        </label>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { isValid } from '@/jsHelper/forms';

export default defineComponent({
  name: 'MultiChoice',
  props: {
    name: {
      type: String,
      required: true,
    },
    modelValue: {
      type: Array,
      default: () => [],
      required: true,
    },
    lists: {
      type: Array,
      default: () => [],
      required: true,
    },
    invalidMessage: {
      type: String,
      default: '',
    },
    forAttrOfLabel: {
      type: String,
      required: true,
    },
    invalidMessageId: {
      type: String,
      required: true,
    },
  },
  emits: ['update:modelValue'],
  data() {
    return {
      checkByKey: 'id',
      selectedItems: this.clone(this.modelValue),
    };
  },
  computed: {
    invalid(): boolean {
      return !isValid({
        type: 'MultiChoice',
        invalidMessage: this.invalidMessage,
      });
    },
  },
  methods: {
    clone(data) {
      return JSON.parse(JSON.stringify(data));
    },
    getItemName(item) {
      return typeof item === 'object' ? item.name : item;
    },
    onCheck(item) {
      // if the item is already selected, remove it from selectedItemsIndex; otherwise push it to modelValue
      if (this.isItemChecked(item)) {
        this.selectedItems = this.selectedItems.filter((selectedItem) => {
          if (typeof selectedItem === 'object') {
            return item[this.checkByKey] !== selectedItem[this.checkByKey];
          }

          return selectedItem !== item;
        });
      } else {
        this.selectedItems.push(item);
      }

      this.$emit('update:modelValue', this.clone(this.selectedItems));
    },
    isItemChecked(item): boolean {
      if (typeof item === 'object') {
        return this.selectedItems.some((selectedItem) => selectedItem[this.checkByKey] === item[this.checkByKey]);
      }

      return this.selectedItems.includes(item);
    },
  },
});
</script>

<style lang="stylus" scoped>
.multi-choice
  background-color: var(--bgc-inputfield-on-container)
  border-radius: var(--border-radius-container)
  height: calc(5 * var(--inputfield-size))
  overflow-y: auto

  &-select
    width: 0
    height: 0
    visibility: hidden

  &-checkboxes
    display: flex
    flex-direction: column
    padding: calc(var(--layout-spacing-unit) / 2) calc(var(--layout-spacing-unit) * 1.5)

    &__checkbox
      display: flex
      align-items: center
      margin-bottom: var(--layout-spacing-unit)

      & label
        width: 100%
        margin: 0 0.25rem

      & div[id*="multi-choice-checkboxes__checkbox--"]
        width: var(--font-size-4)
        height: var(--font-size-4)
        border: 2px solid
        border-radius: 2px
        background-color: transparent
        transition: background-color 250ms, border-color 250ms
        margin-right: var(--layout-spacing-unit-small)
        position: relative

        &[aria-checked=false]
          border-color: var(--font-color-contrast-low)

        &[aria-checked=true]
          border-color: var(--color-accent)

          &:after
            content: "✓"
            display: block
            width: 100%
            height: 100%
            line-height: 120%
            font-size: 0.8rem
            font-weight: bold
            text-align: center
            color: var(--color-accent)
</style>
