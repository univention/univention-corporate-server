<!--
 SPDX-License-Identifier: AGPL-3.0-only
 SPDX-FileCopyrightText: 2023-2024 Univention GmbH
-->

<template>
  <div
    class="suggestion-box"
    tabindex="0"
    @focusout="toggleSuggestionList(false)"
  >
    <div class="suggestion-box-input-group">
      <input
        :id="forAttrOfLabel"
        ref="input"
        :value="value"
        :disabled="disabled"
        :tabindex="tabindex"
        :required="required"
        :name="name"
        :aria-invalid="invalid"
        :aria-describedby="invalidMessageId || undefined"
        data-test="suggestion-box"
        class="suggestion-box-input-group__input"
        @input="updateModelValue"
        @keydown.esc.prevent="toggleSuggestionList(false)"
        @keydown.enter.prevent="onSelectOption(availableOptions[activeOptionIndex])"
        @keydown.arrow-up.prevent="movingOption('up')"
        @keydown.arrow-down.prevent="movingOption('down')"
      >
      <IconButton
        class="suggestion-box-input-group__show-list-button"
        icon="chevron-down"
        aria-label-prop="Open mail domain list"
        role="button"
        @click="toggleSuggestionList(!isSuggestionListOpen, true)"
        @keydown.enter.prevent="activeOptionIndex !== -1 ? onSelectOption(availableOptions[activeOptionIndex]) : toggleSuggestionList(!isSuggestionListOpen, true)"
        @keydown.esc.prevent="toggleSuggestionList(false)"
        @keydown.arrow-up.prevent="movingOption('up')"
        @keydown.arrow-down.prevent="movingOption('down')"
      />
    </div>
    <Transition>
      <div
        v-if="isSuggestionListOpen"
        class="suggestion-box-suggestion-list"
        role="menu"
      >
        <div
          v-for="(option, index) in availableOptions"
          :key="option"
          class="suggestion-box-suggestion-list__option"
          role="menuitem"
          :class="{ 'suggestion-box-suggestion-list__option--selected': index === activeOptionIndex }"
          @click="onSelectOption(option, true)"
        >
          <span
            class="suggestion-box-suggestion-list__option-text"
            role="presentation"
          >
            {{ option }}
          </span>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';
import { isValid } from '@/jsHelper/forms';
import IconButton from '@/components/globals/IconButton.vue';

export default defineComponent({
  name: 'SuggestionBox',
  components: {
    IconButton,
  },
  props: {
    name: {
      type: String,
      required: true,
    },
    forAttrOfLabel: {
      type: String,
      required: true,
    },
    modelValue: {
      type: String,
      required: true,
    },
    invalidMessage: {
      type: String,
      default: '',
    },
    invalidMessageId: {
      type: String,
      required: true,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    tabindex: {
      type: Number,
      default: 0,
    },
    required: {
      type: Boolean,
      default: false,
    },
    suggestedOptions: {
      type: Array as PropType<string[]>,
      required: true,
    },
  },
  emits: ['update:modelValue'],
  data() {
    return {
      isSuggestionListOpen: false,
      activeOptionIndex: -1,
      // isShowListButtonClicked is used to detect if the show list button (arrow icon) is clicked
      // we need this variable because we shouldn't filter options when user click the show list button
      isShowListButtonClicked: false,
      value: '',
    };
  },
  computed: {
    invalid(): boolean {
      return !isValid({
        type: 'SuggestionBox',
        invalidMessage: this.invalidMessage,
      });
    },
    availableOptions(): string[] {
      if (!this.value || this.isShowListButtonClicked) return this.suggestedOptions;
      return this.suggestedOptions.filter((option) => option.toLowerCase().includes(this.value.toLowerCase()));
    },
  },
  watch: {
    isSuggestionListOpen(isOpen: boolean) {
      if (!isOpen) {
        this.activeOptionIndex = -1;
        this.isShowListButtonClicked = false;
      }
    },
  },
  methods: {
    updateModelValue(event: Event): void {
      const target = event.target as HTMLInputElement;
      const value: string = target.value;
      this.toggleSuggestionList(!!value);
      this.value = value;
      this.$emit('update:modelValue', value);
    },
    onSelectOption(option: string, isClick?: boolean): void {
      // if isClick is true, it means that the user clicked on the option (line 47)
      // so we don't need to close the suggestion list or find the closest form
      if (isClick || this.activeOptionIndex !== -1) {
        this.value = option;
        this.isSuggestionListOpen = false;
        this.$emit('update:modelValue', option);
        return;
      }
      // if activeOptionIndex === -1 means the suggestion list is closed, so we need to submit the form as natively as possible
      // we need to do this because we override the keydown.enter event of the input element when the suggestion list is open
      if (this.activeOptionIndex === -1) {
        this.onSubmitForm();
      }
    },
    onSubmitForm(): void {
      const form = this.$el.closest('form');
      if (form) {
        form.submit();
      }
    },
    toggleSuggestionList(isOpen?: boolean, isShowListButtonClicked?: boolean): void {
      this.isSuggestionListOpen = isOpen !== undefined ? isOpen : !this.isSuggestionListOpen;
      if (isShowListButtonClicked !== undefined) this.isShowListButtonClicked = isShowListButtonClicked;
    },
    movingOption(direction: 'up' | 'down'): void {
      if (!this.isSuggestionListOpen) {
        this.toggleSuggestionList(true);
      }
      if (direction === 'up') {
        this.activeOptionIndex -= 1;
        if (this.activeOptionIndex < 0) {
          this.activeOptionIndex = this.availableOptions.length - 1;
        }
      } else {
        this.activeOptionIndex += 1;
        if (this.activeOptionIndex >= this.availableOptions.length) {
          this.activeOptionIndex = 0;
        }
      }
    },
  },
});
</script>

<style lang="stylus">
.suggestion-box
  width: fit-content

  &-input-group
    position: relative

    &__input
      margin-bottom: 0

    &__show-list-button
      position: absolute
      top: var(--layout-spacing-unit-small)
      right: 0

  &-suggestion-list
      display: flex
      flex-direction: column
      width: 100%
      &__option
        padding: var(--layout-spacing-unit)
        background-color: var(--bgc-popup)
        font-size: var(--font-size-4)
        cursor: pointer

        &--selected, &:hover
          background-color: var(--bgc-popup-item-hover) !important
        &--highlight
          background-color: var(--bgc-popup-item-selected) !important

        &:first-child
          border-top-left-radius: var(--border-radius-interactable)
          border-top-right-radius: var(--border-radius-interactable)

        &:last-child
          border-bottom-left-radius: var(--border-radius-interactable)
          border-bottom-right-radius: var(--border-radius-interactable)
</style>
