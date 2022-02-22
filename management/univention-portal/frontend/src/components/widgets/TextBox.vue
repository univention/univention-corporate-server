<template>
  <input
    :id="forAttrOfLabel"
    ref="input"
    :name="name"
    type="text"
    :value="modelValue"
    :aria-invalid="invalid"
    :aria-describedby="invalidMessageId"
    data-test="text-box"
    @input="$emit('update:modelValue', $event.target.value)"
  >
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { isValid } from '@/jsHelper/forms';

export default defineComponent({
  name: 'TextBox',
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
  },
  emits: ['update:modelValue'],
  computed: {
    invalid(): boolean {
      return !isValid({
        type: 'TextBox',
        invalidMessage: this.invalidMessage,
      });
    },
  },
  methods: {
    focus() {
      // @ts-ignore TODO
      this.$refs.input.focus();
    },
  },
});
</script>
