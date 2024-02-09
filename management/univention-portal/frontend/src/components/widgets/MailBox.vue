<!--
 SPDX-License-Identifier: AGPL-3.0-only
 SPDX-FileCopyrightText: 2023-2024 Univention GmbH
-->

<template>
  <div
    ref="mailbox"
    class="mailbox"
    tabindex="0"
    @focusout="toggleDomainList(false)"
  >
    <input
      :id="forAttrOfLabel"
      ref="input"
      v-model="mailValue"
      :input="mailValue"
      :disabled="disabled"
      :tabindex="tabindex"
      :required="required"
      :name="name"
      :type="inputType"
      :aria-invalid="invalid"
      :aria-describedby="invalidMessageId || undefined"
      data-test="mail-box"
      @keydown.enter.prevent="selectDomainOption(activeDomainIndex)"
      @keydown.esc.prevent="toggleDomainList(false)"
      @keydown.arrow-up.prevent="movingDomainOption('up')"
      @keydown.arrow-down.prevent="movingDomainOption('down')"
    >
    <IconButton
      class="mailbox__icon-button"
      icon="chevron-down"
      aria-label-prop="Open mail domain list"
      @click="toggleDomainList"
      @keydown.enter.prevent="toggleDomainList()"
      @keydown.esc.prevent="toggleDomainList(false)"
      @keydown.arrow-up.prevent="movingDomainOption('up')"
      @keydown.arrow-down.prevent="movingDomainOption('down')"
    />
    <Transition>
      <div
        v-if="isDomainListOpen"
        class="mailbox__domain-list"
      >
        <div
          v-for="(availableMailDomain, index) in availableMailDomains"
          :key="index"
          :class="['mailbox__domain-list-option', { 'mailbox__domain-list-option--selected': index === activeDomainIndex }]"
          @click="selectDomainOption(index)"
        >
          <mark class="mailbox__domain-list-option--highlight">
            {{ domainText(mailPrefix, availableMailDomain).hightlightPart }}
          </mark>{{ domainText(mailPrefix, availableMailDomain).nonHightlightPart }}
        </div>
      </div>
    </Transition>
  </div>
</template>

<script lang="ts">
import { defineComponent, nextTick } from 'vue';
import { isValid } from '@/jsHelper/forms';
import IconButton from '@/components/globals/IconButton.vue';

interface MailBoxData {
  mailValue: string;
  isDomainListOpen: boolean;
  selectedDomainIndex: number | null;
  activeDomainIndex: number;
  availableMailDomains: string[];
  inputType: 'email' | 'text';
}
export default defineComponent({
  name: 'MailBox',
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
    domainList: {
      type: Array as () => string[],
      required: true,
    },
  },
  emits: ['update:modelValue'],
  data(): MailBoxData {
    return {
      mailValue: '',
      activeDomainIndex: -1,
      selectedDomainIndex: null,
      isDomainListOpen: false,
      availableMailDomains: [],
      // because of the email type does not support the setSelectionRange method (https://stackoverflow.com/questions/26658474/)
      // we need to use the text type instead (when using the setSelectionRange method), otherwise, the type will be email
      inputType: 'email',
    };
  },
  computed: {
    invalid(): boolean {
      return !isValid({
        type: 'MailBox',
        invalidMessage: this.invalidMessage,
      });
    },
    mailPrefix(): string {
      if (this.mailValue.includes('@')) return this.mailValue.split('@')[0];
      return this.mailValue;
    },
    mailDomain(): string {
      if (this.mailValue.includes('@')) return this.mailValue.split('@')[1];
      return '';
    },
  },
  watch: {
    mailValue(value: string) {
      this.$emit('update:modelValue', value);
      // if the value is just selected from the domain list, we don't need to change the isDomainListOpen state
      if (this.selectedDomainIndex !== null) {
        this.selectedDomainIndex = null;
        return;
      }
      if (value.includes('@')) {
        this.isDomainListOpen = true;
        return;
      }
      this.isDomainListOpen = false;
    },
    isDomainListOpen(isOpen: boolean) {
      if (!isOpen) {
        this.activeDomainIndex = -1;
        this.inputType = 'email';
      }
      this.updateAvailableDomains();
    },
    mailDomain() {
      if (this.activeDomainIndex !== -1 && this.isDomainListOpen) return;
      this.updateAvailableDomains();
    },
  },
  mounted() {
    this.updateAvailableDomains();
  },
  methods: {
    toggleDomainList(isDomainListOpen?: boolean) {
      this.isDomainListOpen = isDomainListOpen ?? !this.isDomainListOpen;
    },
    domainText(mailPrefix: string, mailDomain: string) {
      const mail = `${mailPrefix}@${mailDomain}`;
      const text = {
        hightlightPart: '',
        nonHightlightPart: mail,
      };
      if (mail.includes(this.mailValue)) {
        text.hightlightPart = mail.substring(
          mail.indexOf(this.mailValue), this.mailValue.length,
        );
        text.nonHightlightPart = mail.substring(
          this.mailValue.length,
        );
      }
      return text;
    },
    movingDomainOption(direction: 'up' | 'down') {
      if (!this.isDomainListOpen) {
        this.toggleDomainList(true);
        return;
      }
      if (direction === 'up') {
        this.activeDomainIndex -= 1;
        if (this.activeDomainIndex < 0) {
          this.activeDomainIndex = this.availableMailDomains.length - 1;
        }
      } else {
        this.activeDomainIndex += 1;
        if (this.activeDomainIndex >= this.availableMailDomains.length) {
          this.activeDomainIndex = 0;
        }
      }

      const mailValue = `${this.mailPrefix}@${this.availableMailDomains[this.activeDomainIndex]}`;
      this.mailValue = mailValue;

      const start = this.mailPrefix.length + 1;
      const end = mailValue.length;
      // set selection range to the end of the mail domain
      this.setInputSelectionRange(start, end);
    },
    selectDomainOption(index: number) {
      // if index === -1 means the domain list is closed, so we need to submit the form as natively as possible
      // we need to do this because we override the keydown.enter event of the input element when the domain list is open
      if (index === -1) {
        // find the form element and submit it
        const form = this.$el.closest('form');
        if (form) {
          form.submit();
        }
        return;
      }
      this.mailValue = `${this.mailPrefix}@${this.availableMailDomains[index]}`;
      this.selectedDomainIndex = index;
      this.toggleDomainList(false);
    },
    updateAvailableDomains() {
      this.availableMailDomains = this.domainList && this.domainList.filter(
        (mailDomain) => mailDomain.includes(this.mailDomain),
      );
    },
    setInputSelectionRange(start: number, end: number) {
      const input = this.$refs.input as HTMLInputElement;
      nextTick(() => {
        input.type = 'text';
        input.focus();
        input.setSelectionRange(start, end);
      });
    },
  },
});
</script>

<style lang="stylus">
.mailbox
  width: fit-content
  position: relative
  &__icon-button
    position: absolute
    top: var(--layout-spacing-unit-small)
    right: 0
  &__domain-list
    display: flex
    flex-direction: column
    &-option
      padding: var(--layout-spacing-unit)
      border-radius: var(--border-radius-interactable)
      background-color: var(--bgc-popup)
      font-size: var(--font-size-4)
      cursor: pointer
      &--selected, &:hover
        background-color: var(--bgc-popup-item-hover)
      &--highlight
        background-color: var(--bgc-popup-item-selected) !important
</style>
