<template>
  <div class="password-box">
    <input
      :id="forAttrOfLabel"
      ref="input"
      :disabled="disabled"
      :tabindex="tabindex"
      :required="required"
      :name="name"
      type="password"
      :value="modelValue"
      :aria-invalid="invalid"
      :aria-describedby="invalidMessageId || null"
      data-test="password-box"
      @input="$emit('update:modelValue', $event.target.value)"
    >
    <toggle-button
      v-if="canShowPassword"
      :disabled="disabled"
      :tabindex="tabindex"
      :toggle-icons="passwordIcons"
      :toggle-labels="TOGGLE_PASSWORD"
      class="password-box__icon"
      data-test="password-box-icon"
      :is-toggled="showPassword"
      @update:is-toggled="updateShowPassword"
    />
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { isValid } from '@/jsHelper/forms';
import _ from '@/jsHelper/translate';

import ToggleButton from '@/components/widgets/ToggleButton.vue';

export default defineComponent({
  name: 'PasswordBox',
  components: {
    ToggleButton,
  },
  props: {
    name: {
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
    };
  },
  computed: {
    invalid(): boolean {
      return !isValid({
        type: 'PasswordBox',
        invalidMessage: this.invalidMessage,
      });
    },
    TOGGLE_PASSWORD(): Record<string, string> {
      return {
        initial: _('Show password'),
        toggled: _('Hide password'),
      };
    },
    passwordIcons(): Record<string, string> {
      return {
        initial: 'eye-off',
        toggled: 'eye',
      };
    },
  },
  methods: {
    focus(): void {
      // @ts-ignore
      this.$refs.input.focus();
    },
    updateShowPassword(newValue) {
      this.showPassword = newValue;
      (this.$refs.input as HTMLInputElement).type = newValue ? 'text' : 'password';
    },
  },
});
</script>

<style lang="stylus">
.password-box
  position: relative

  &__icon {
    position: absolute
    right: 0
    top: 50%
    transform: translateY(-50%)
  }
</style>
