<!--
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
-->
<template>
  <div
    class="locale-input"
    data-test="locale-input"
  >
    <div class="locale-input__wrapper">
      <input
        :id="forAttrOfLabel"
        ref="input"
        :value="modelValue.en_US"
        class="locale-input__text-field"
        autocomplete="off"
        :name="name"
        :tabindex="tabindex"
        :required="required"
        :aria-invalid="invalid"
        :aria-describedby="invalidMessageId || null"
        :data-test="`localeInput--${i18nLabel}`"
        @input="onInputEN"
      >
      <icon-button
        :id="`locale-input__icon--${i18nLabel}`"
        icon="globe"
        class="locale-input__button"
        :has-button-style="true"
        :aria-label-prop="TRANSLATE_TEXT_INPUT"
        :tabindex="tabindex"
        :data-test="`iconButton--${i18nLabel}`"
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
import { isValid } from '@/jsHelper/forms';

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
    required: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['update:modelValue'],
  computed: {
    TRANSLATE_TEXT_INPUT(): string {
      return _('Edit Translations');
    },
    translationEditingDialogLevel(): number {
      return this.isInModal ? 2 : 1;
    },
    invalid(): boolean {
      return !isValid({
        type: 'TextBox',
        invalidMessage: this.invalidMessage,
      });
    },
  },
  methods: {
    onInputEN(evt) {
      const newVal = JSON.parse(JSON.stringify(this.modelValue));
      newVal.en_US = evt.target.value;
      this.$emit('update:modelValue', newVal);
    },
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
      })
        .then((data) => {
          this.$emit('update:modelValue', data.translations);
        }, () => {
          // catch modal/reject to prevent uncaught reject error in console
        })
        .finally(() => {
          this.$store.dispatch('modal/hideAndClearModal', this.translationEditingDialogLevel);
          this.$store.dispatch('activity/setRegion', 'modal-wrapper--isVisible-1');
        });
      this.$store.dispatch('activity/setLevel', 'modal2');
      this.$store.dispatch('activity/saveFocus', {
        region: 'modal-wrapper--isVisible-1',
        id: `locale-input__icon--${this.i18nLabel}`,
      });
    },
    focus() {
      // @ts-ignore TODO
      this.$refs.input.focus();
    },
  },
});
</script>

<style lang="stylus">
.locale-input
  &__wrapper
    display: flex
    align-items: center
    gap: var(--layout-spacing-unit)

  &__button
    flex: 0 0 auto
</style>
