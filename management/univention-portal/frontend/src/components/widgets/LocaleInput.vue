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
  <div class="locale-input">
    <label
      v-for="locale in locales"
      :key="locale"
    >
      {{ label }} ({{ locale }})
      <input
        v-model="modelValueData[locale]"
        :name="locale === 'en_US' ? name : `${name}-${locale}`"
        autocomplete="off"
        tabindex="0"
      >
    </label>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';
import { mapGetters } from 'vuex';

import Translate from '@/i18n/Translate.vue';

export default defineComponent({
  name: 'LocaleInput',
  components: {
    Translate,
  },
  props: {
    modelValue: {
      type: Object as PropType<Record<string, string>>,
      required: true,
    },
    name: {
      type: String,
      required: true,
    },
    label: {
      type: String,
      required: true,
    },
  },
  emits: [
    'update:modelValue',
  ],
  data() {
    return {
      modelValueData: {},
    };
  },
  computed: {
    ...mapGetters({
      locales: 'locale/getAvailableLocales',
      getModalError: 'modal/getModalError',
    }),
  },
  created() {
    const model = this.modelValue;
    const newModel = {};

    if ('locale' in model) {
      newModel[model.locale] = model.value;
      Object.assign(this.modelValueData, newModel);
    } else {
      Object.assign(this.modelValueData, model);
    }
  },
  updated() {
    this.$emit('update:modelValue', this.modelValueData);
  },
});
</script>

<style lang="stylus">
.locale-input
  margin-top: calc(3 * var(--layout-spacing-unit))

  label
    margin-top: 0
</style>
