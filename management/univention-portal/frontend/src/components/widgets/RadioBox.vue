<template>
  <div
    class="radio-box"
    data-test="radio-box"
  >
    <label
      v-for="option in options"
      :key="option"
      :for="`${name}--${option.id}`"
      class="radio-box__label"
    >
      <input
        :id="`${name}--${option.id}`"
        type="radio"
        :tabindex="tabindex"
        name="radio-input"
        :value="option.id"
        class="radio-box__input"
        :checked="modelValue === option.id"
        @change="$emit('update:modelValue', option.id)"
      >
      {{ option.label }}
    </label>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { isValid } from '@/jsHelper/forms';

export default defineComponent({
  name: 'RadioBox',
  props: {
    modelValue: {
      type: String,
      required: true,
    },
    invalidMessage: {
      type: String,
      default: '',
    },
    options: {
      type: Array,
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
  computed: {
    invalid(): boolean {
      return !isValid({
        type: 'RadioBox',
        invalidMessage: this.invalidMessage,
      });
    },
  },
  methods: {
    focus(): void {
      console.warn('Focus not implemented');
    },
  },
});
</script>
<style lang="stylus">
.radio-box
  &__label
    display: flex
    align-items: center
</style>
