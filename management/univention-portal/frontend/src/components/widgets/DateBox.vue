<template>
  <input
    :id="forAttrOfLabel"
    ref="input"
    :name="name"
    type="date"
    :value="modelValue"
    :aria-invalid="invalid"
    :aria-describedby="invalidMessageId || null"
    data-test="date-box"
    @input="$emit('update:modelValue', $event.target.value)"
  >
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { isValid } from '@/jsHelper/forms';

export default defineComponent({
  name: 'DateBox',
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
        type: 'DateBox',
        invalidMessage: this.invalidMessage,
      });
    },
  },
  methods: {
    focus() {
      // @ts-ignore
      this.$refs.input.focus();
    },
  },
});
</script>
