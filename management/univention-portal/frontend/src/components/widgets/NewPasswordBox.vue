<!--
 SPDX-License-Identifier: AGPL-3.0-only
 SPDX-FileCopyrightText: 2023-2024 Univention GmbH
-->

<template>
  <div class="new-password-box">
    <div class="password-box">
      <input
        :id="forAttrOfLabel"
        ref="inputNew"
        :disabled="disabled"
        :tabindex="tabindex"
        :required="required"
        :name="name"
        type="password"
        :value="modelValue.newPassword"
        :aria-invalid="invalidNew"
        :aria-describedby="invalidMessageId || undefined"
        data-testid="new-password-box"
        @input="updateModelValue($event, 'newPassword')"
      >
      <toggle-button
        v-if="canShowPassword"
        :disabled="disabled"
        :tabindex="tabindex"
        :toggle-icons="passwordIconsNew"
        :toggle-labels="TOGGLE_PASSWORD"
        class="password-box__icon"
        data-test="password-box-icon"
        :is-toggled="showPasswordNew"
        @update:is-toggled="updateShowPasswordNew"
      />
    </div>
    <input-error-message
      :id="invalidMessageId"
      :display-condition="errorDisplayConditionNew"
      :error-message="invalidMessage.invalidMessageNew"
    />
    <form-label
      :label="PASSWORD_RETYPE_LABEL"
      aria-label="widget.ariaLabel || widget.label"
      for-attr="forAttrOfLabel"
      :invalid-message="invalidMessage.invalidMessageRetype"
      data-test="form-element-label"
      class="password-box__retype-formlabel"
    />
    <div class="password-box">
      <input
        :id="forAttrOfLabelRetype"
        ref="inputRetype"
        :value="modelValue.retypePassword"
        :disabled="disabled"
        :tabindex="tabindex"
        :required="required"
        :name="name"
        type="password"
        :aria-invalid="invalidRetype"
        :aria-describedby="invalidMessageIdRetype || undefined"
        data-testid="retype-password-box"
        @input="updateModelValue($event, 'retypePassword')"
      >
      <toggle-button
        v-if="canShowPassword"
        :disabled="disabled"
        :tabindex="tabindex"
        :toggle-icons="passwordIconsRetype"
        :toggle-labels="TOGGLE_PASSWORD"
        class="password-box__icon"
        data-test="password-box-icon"
        :is-toggled="showPasswordRetype"
        @update:is-toggled="updateShowPasswordRetype"
      />
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';
import _ from '@/jsHelper/translate';
import { isValid } from '@/jsHelper/forms';

import FormLabel from '@/components/forms/FormLabel.vue';
import InputErrorMessage from '@/components/forms/InputErrorMessage.vue';
import PasswordBox from '@/components/widgets/PasswordBox.vue';
import ToggleButton from './ToggleButton.vue';

export default defineComponent({
  name: 'NewPasswordBox',
  components: {
    PasswordBox,
    FormLabel,
    InputErrorMessage,
    ToggleButton,
  },
  props: {
    name: {
      type: String,
      required: true,
    },
    modelValue: {
      type: Object as PropType<Record<string, string>>,
      required: true,
    },
    invalidMessage: {
      type: Object as PropType<Record<string, string>>,
      default: {
        invalidMessageNew: '',
        invalidMessageRetype: '',
      },
    },
    forAttrOfLabel: {
      type: String,
      required: true,
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
    canShowPassword: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['update:modelValue'],
  data() {
    return {
      showPassword: false,
      newModelValue: {
        newPassword: this.modelValue.newPassword,
        retypePassword: this.modelValue.retypePassword,
      },
      invalidMessageIdRetype: '',
      forAttrOfLabelRetype: '',
      showPasswordNew: false,
      showPasswordRetype: false,
    };
  },
  computed: {
    invalid(): boolean {
      return !isValid({
        type: 'NewPasswordBox',
        invalidMessage: this.invalidMessage,
      });
    },
    TOGGLE_PASSWORD(): Record<string, string> {
      return {
        initial: _('Show password'),
        toggled: _('Hide password'),
      };
    },
    passwordIconsNew(): Record<string, string> {
      return {
        initial: 'eye-off',
        toggled: 'eye',
      };
    },
    passwordIconsRetype(): Record<string, string> {
      return {
        initial: 'eye-off',
        toggled: 'eye',
      };
    },
    PASSWORD_RETYPE_LABEL(): string {
      return _('New password (retype)');
    },
    errorDisplayConditionNew(): boolean {
      return typeof this.invalidMessage !== 'string' && this.invalidMessage.invalidMessageNew !== '';
    },
    invalidNew(): boolean {
      return typeof this.invalidMessage !== 'string' && this.invalidMessage.invalidMessageNew !== '';
    },
    invalidRetype(): boolean {
      return typeof this.invalidMessage !== 'string' && this.invalidMessage.invalidMessageRetype !== '';
    },
  },
  methods: {
    /**
     * Focus either the password input box, or the 'retype' box.
     *
     * If one of the inputs is invalid, focus that one.
     * If both are valid, focus the first one.
     */
    focus(): void {
      if (this.invalidNew) {
        (this.$refs.inputNew as HTMLInputElement).focus();
      } else if (this.invalidRetype) {
        (this.$refs.inputRetype as HTMLInputElement).focus();
      } else {
        (this.$refs.inputNew as HTMLInputElement).focus();
      }
    },
    updateShowPasswordNew(newValue) {
      this.showPasswordNew = newValue;
      (this.$refs.inputNew as HTMLInputElement).type = newValue ? 'text' : 'password';
    },
    updateShowPasswordRetype(newValue) {
      this.showPasswordRetype = newValue;
      (this.$refs.inputRetype as HTMLInputElement).type = newValue ? 'text' : 'password';
    },
    updateModelValue(event, inputType) {
      const value = event?.target?.value;
      this.newModelValue[inputType] = value;
      this.$emit('update:modelValue', this.newModelValue);
    },
  },
});
</script>

<style lang="stylus">
.password-box
  position: relative

  &__retype-formlabel {
    margin-top: calc(3 * var(--layout-spacing-unit))!important;
  }

  &__icon {
    position: absolute
    right: 0
    top: 50%
    transform: translateY(-50%)
  }
</style>
