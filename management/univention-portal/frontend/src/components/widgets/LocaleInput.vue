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
      class="locale-input__label"
      :for="`locale-input-${I18N_LABEL}`"
    >
      {{ I18N_LABEL }}
    </label>
    <div class="locale-input__wrapper">
      <input
        :id="`locale-input-${I18N_LABEL}`"
        v-model="modelValueData.en_US"
        class="locale-input__text-field"
        autocomplete="off"
        :name="name"
        :tabindex="tabindex"
        :data-test="`localeInput--${I18N_LABEL}`"
      >
      <icon-button
        :id="`locale-input__icon--${I18N_LABEL}`"
        icon="globe"
        :has-button-style="true"
        :aria-label-prop="TRANSLATE_TEXT_INPUT"
        :tabindex="tabindex"
        :data-test="`iconButton--${I18N_LABEL}`"
        @click="openTranslationEditingDialog"
      />
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';
import { mapGetters } from 'vuex';
import _ from '@/jsHelper/translate';

import IconButton from '@/components/globals/IconButton.vue';

export default defineComponent({
  name: 'LocaleInput',
  components: {
    IconButton,
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
    i18nLabel: {
      type: String,
      required: true,
    },
    tabindex: {
      type: Number,
      default: 0,
    },
    isInModal: {
      type: Boolean,
      default: true,
    },
  },
  emits: [
    'update:modelValue',
  ],
  data() {
    return {
      modelValueData: {
        en_US: '',
      },
      translations: {
        en_US: '',
      },
    };
  },
  computed: {
    ...mapGetters({
      locales: 'locale/getAvailableLocales',
      getModalError: 'modal/getModalError',
      savedFocus: 'activity/focus',
    }),
    I18N_LABEL():string {
      return _('%(key1)s', { key1: this.i18nLabel });
    },
    TRANSLATE_TEXT_INPUT(): string {
      return _('Edit Translations');
    },
    hasNewTranslation(): string {
      return !this.translations.en_US ? this.translations.en_US : this.modelValueData.en_US;
    },
    translationEditingDialogLevel(): number {
      return this.isInModal ? 2 : 1;
    },
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
  methods: {
    openTranslationEditingDialog() {
      this.$store.dispatch('modal/setShowModalPromise', {
        level: this.translationEditingDialogLevel,
        name: 'TranslationEditing',
        stubborn: true,
        props: {
          inputValue: this.modelValue,
          title: this.i18nLabel,
          modalLevelProp: this.translationEditingDialogLevel,
        },
      }).then((data) => {
        this.$store.dispatch('modal/hideAndClearModal', this.translationEditingDialogLevel);
        this.modelValueData = data.translations;
        this.translations = data.translations;
        const clickedButton = document.getElementById(`locale-input__icon--${this.I18N_LABEL}`);
        clickedButton?.focus();
      }, () => {
        this.$store.dispatch('modal/hideAndClearModal', this.translationEditingDialogLevel);
      });
      this.$store.dispatch('activity/setRegion', 'translation-editing');
      this.$store.dispatch('activity/setLevel', 'modal2');
      this.$store.dispatch('activity/saveFocus', {
        region: 'modal-wrapper--isVisible',
        id: `locale-input__icon--${this.I18N_LABEL}`,
      });
    },
  },
});
</script>

<style lang="stylus">
.locale-input
  margin-top: calc(3 * var(--layout-spacing-unit))
  margin-bottom: var(--layout-spacing-unit)

  label
    margin-top: 0
  &__wrapper
    display: flex
    align-items: center

  &__text-field
    margin-bottom: 0
    margin-right: var(--layout-spacing-unit)

</style>
