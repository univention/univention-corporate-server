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
  <div>
    <div
      v-for="(link, index) in modelValueData"
      :key="index"
      class="link-widget"
    >
      <div class="link-widget__select">
        <select
          v-model="modelValueData[index].locale"
          :tabindex="tabindex"
          :aria-label="localeSelect(index)"
        >
          <option
            v-for="select in locales"
            :key="select"
            :selected="modelValueData[index].locale || select"
            class="link-widget__option"
          >
            {{ select }}
          </option>
        </select>
      </div>
      <div class="link-widget__input">
        <input
          :ref="`link${index}`"
          v-model="modelValueData[index].value"
          :name="index === 0 ? name : `${name}-${index}`"
          :tabindex="tabindex"
          :aria-label="linkInput(index)"
          autocomplete="off"
        >
      </div>
      <div
        v-if="modelValueData.length > 1"
        class="link-widget__remove modal-admin__button"
      >
        <icon-button
          icon="trash"
          :aria-label-prop="removeLink(index)"
          :active-at="['modal']"
          :has-button-style="true"
          :data-test="`link-widget-remove-button-${index}`"
          @click="removeField(index, modelValueData)"
        />
      </div>
    </div>
    <div class="modal-admin__button">
      <button
        ref="addButton"
        type="button"
        class="modal-admin__button--inner"
        data-test="add-field"
        :tabindex="tabindex"
        @click.prevent="addField()"
      >
        <portal-icon
          icon="plus"
        />
        {{ ADD_LINK }}
      </button>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';
import { mapGetters } from 'vuex';
import _ from '@/jsHelper/translate';

import IconButton from '@/components/globals/IconButton.vue';
import PortalIcon from '@/components/globals/PortalIcon.vue';

interface LinkWidgetData {
  modelValueData: Array<unknown>,
}

interface LocaleAndValue {
  locale: string,
  value: string,
}

export default defineComponent({
  name: 'LinkWidget',
  components: {
    IconButton,
    PortalIcon,
  },
  props: {
    modelValue: {
      type: Array as PropType<LocaleAndValue[]>,
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
  data(): LinkWidgetData {
    return {
      modelValueData: [],
    };
  },
  computed: {
    ...mapGetters({
      locales: 'locale/getAvailableLocales',
      currentLocale: 'locale/getLocale',
    }),
    REMOVE(): string {
      return _('Remove');
    },
    ADD_LINK(): string {
      return _('Add link');
    },
  },
  created() {
    this.modelValue.forEach((val) => {
      this.modelValueData.push({
        locale: val.locale,
        value: val.value,
      });
    });
    this.modelValueData.push({
      locale: 'en_US',
      value: '',
    });
  },
  updated() {
    this.$emit('update:modelValue', this.modelValueData);
  },
  methods: {
    addField() {
      this.modelValueData.push({ locale: this.currentLocale || 'en_US', value: '' });
      const i = (this.modelValueData.length - 1);

      // @ts-ignore FIXME not sure how to fix this error
      this.$nextTick(() => {
        const elem = (this.$refs[`link${i}`] as HTMLElement);
        elem.focus();
      });
    },
    removeField(index) {
      this.modelValueData.splice(index, 1);
    },
    LINK(index: number): string {
      return `${_('Link')} ${index + 1}:`;
    },
    localeSelect(index: number): string {
      return `${this.LINK(index)} ${_('Select locale for Link')}`;
    },
    linkInput(index: number): string {
      return `${this.LINK(index)} ${_('insert valid Link')}`;
    },
    removeLink(index: number): string {
      return `${this.LINK(index)} ${this.REMOVE}`;
    },
    focus() {
      // @ts-ignore TODO
      this.$refs.addButton.focus();
    },
  },
});

export { LocaleAndValue };

</script>

<style lang="stylus">
.link-widget
  display: flex
  align-items: center
  margin-bottom: var(--layout-spacing-unit)

  &__select
    flex: 0 0 auto

  &__input
    margin-left: var(--layout-spacing-unit)
    margin-right: var(--layout-spacing-unit)

    input
      width: 100%

  &__remove
    flex: 0 0 auto
</style>
