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
    :id="id"
    :title="TRANSLATION_OF"
    :modal-level="modalLevel"
    @cancel="cancel"
  >
    <form class="translation-editing">
      <label
        v-for="locale in locales"
        :key="locale"
      >
        {{ localeLabel(locale) }}
        <template
          v-if="locale === 'en_US'"
        >
          <required-field-label />
        </template>
        <input
          :ref="'ref_input_' + locale"
          v-model="translationObject[locale]"
          :placeholder="hasValue(locale)"
          class="translation-editing__text-input"
        >
      </label>
      <footer class="translation-editing__footer-buttons">
        <button
          type="button"
          @click.prevent="cancel()"
        >
          {{ CANCEL }}
        </button>
        <button
          class="primary"
          type="button"
          @click.prevent="closeDialog()"
        >
          {{ SAVE }}
        </button>
      </footer>
    </form>
  </modal-dialog>
</template>
<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';
import _ from '@/jsHelper/translate';

import RequiredFieldLabel from '@/components/forms/RequiredFieldLabel.vue';
import ModalDialog from '@/components/modal/ModalDialog.vue';
import ModalWrapper from '@/components/modal/ModalWrapper.vue';

import { Locale } from '@/store/modules/locale/locale.models';

export default defineComponent({
  name: 'TranslationEditing',
  components: {
    ModalDialog,
    ModalWrapper,
    RequiredFieldLabel,
  },
  props: {
    title: {
      type: String,
      default: 'REMOVE',
    },
    inputValue: {
      type: Object,
      required: true,
    },
    modalLevelProp: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      translationObject: {},
      id: '',
    };
  },
  computed: {
    ...mapGetters({
      locales: 'locale/getAvailableLocales',
      localeLabels: 'locale/getLocaleLabels',
      getModalError: 'modal/getModalError',
      savedFocus: 'activity/focus',
    }),
    TRANSLATION_OF(): string {
      return _('Translation: %(key1)s', { key1: this.title });
    },
    CANCEL(): string {
      return _('Cancel');
    },
    SAVE(): string {
      return _('Save');
    },
    modalLevel(): string {
      // Modal 2 Because it set the correct tabindizies for elements in modal Level 1
      return 'modal2';
    },
  },
  mounted() {
    this.locales.forEach((key, index) => {
      if (this.inputValue[this.locales[index]]) {
        this.translationObject[this.locales[index]] = this.inputValue[this.locales[index]];
      }
    });
    this.id = 'translation-editing';

    setTimeout(() => {
      (this.$refs.ref_input_en_US as HTMLElement).focus();
    }, 100);
  },
  methods: {
    cancel(): void {
      this.$store.dispatch('modal/hideAndClearModal', this.modalLevelProp);
      const lastFocusID = this.savedFocus['modal-wrapper--isVisible'];
      const clickedButton = document.getElementById(lastFocusID);
      clickedButton?.focus();
    },
    closeDialog(): void {
      const translations = this.translationObject;
      this.$store.dispatch('modal/resolve', {
        level: this.modalLevelProp,
        translations,
      });
    },
    hasValue(locale): string {
      return this.inputValue[locale] ? null : this.inputValue.en_US;
    },
    isUserInput(locale): boolean {
      return this.inputValue[locale];
    },
    localeLabel(locale: Locale): string {
      return this.localeLabels[locale] || locale;
    },
  },
});

</script>

<style lang="stylus">
.translation-editing
  &__footer-buttons
    display: flex
    justify-content: space-between

  &__text-input
    width: 100%
</style>
