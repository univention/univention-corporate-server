<template>
  <input
    :id="forAttrOfLabel"
    ref="input"
    :name="name"
    type="time"
    :value="modelValue"
    :step="step"
    :aria-invalid="invalid"
    :aria-describedby="invalidMessageId || null"
    data-test="time-box"
    @input="$emit('update:modelValue', $event.target.value)"
  >
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { isValid } from '@/jsHelper/forms';

export default defineComponent({
  name: 'TimeBox',
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
    step: {
      type: Number,
      default: 60,
    },
  },
  emits: ['update:modelValue'],
  computed: {
    invalid(): boolean {
      return !isValid({
        type: 'TimeBox',
        invalidMessage: this.invalidMessage,
      });
    },
  },
  methods: {
    focus() {
      (this.$refs.input as HTMLInputElement).focus();
    },
  },
});
</script>
