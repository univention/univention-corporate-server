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
  <div>
    <div
      v-for="(link, index) in modelValueData"
      :key="index"
      class="link-widget"
    >
      <span class="link-widget__select">
        <select
          v-model="modelValueData[index].locale"
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
      </span>
      <span class="link-widget__input">
        <input
          :ref="`link${index}`"
          v-model="modelValueData[index].value"
        >
      </span>
      <span
        v-if="modelValueData.length > 1"
        class="link-widget__remove modal-admin__button"
      >
        <header-button
          aria-label="Remove link"
          icon="trash"
          :no-click="true"
          @click.stop.prevent="removeField(index, modelValueData)"
        />
      </span>
    </div>
    <span class="modal-admin__button">
      <button
        class="modal-admin__button--inner"
        @click.prevent="addField"
      >
        <portal-icon
          icon="plus"
        />
        <translate
          i18n-key="NEW_ENTRY"
        />
      </button>
    </span>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';
import { mapGetters } from 'vuex';

import HeaderButton from '@/components/navigation/HeaderButton.vue';
import PortalIcon from '@/components/globals/PortalIcon.vue';
import Translate from '@/i18n/Translate.vue';

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
    HeaderButton,
    PortalIcon,
    Translate,
  },
  props: {
    modelValue: {
      type: Array as PropType<LocaleAndValue[]>,
      required: true,
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
  },
  created() {
    this.modelValue.forEach((val) => {
      this.modelValueData.push({
        locale: val.locale,
        value: val.value,
      });
    });
  },
  updated() {
    this.$emit('update:modelValue', this.modelValueData);
  },
  methods: {
    addField() {
      this.modelValueData.push({ locale: this.currentLocale || 'en_US', value: '' });
      const i = (this.modelValueData.length - 1);

      setTimeout(() => {
        const elem = (this.$refs[`link${i}`] as HTMLElement);
        elem.focus();
      }, 50);
    },
    removeField(index) {
      this.modelValueData.splice(index, 1);
    },
  },
});

export { LocaleAndValue };

</script>

<style lang="stylus">
.link-widget
  display: flex
  align-items: center

  &__select
    max-width: 5rem

    select
      width: 5rem

  &__input
    width: 100%
    margin-left: 0.5rem
    margin-right: 2rem

    input
      width: 100%

  &__remove
    width: 3rem
</style>
