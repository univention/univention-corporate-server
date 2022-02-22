<template>
  <input
    :id="forAttrOfLabel"
    ref="input"
    :name="name"
    type="checkbox"
    :checked="modelValue"
    :aria-invalid="invalid"
    :aria-describedby="invalidMessageId"
    @change="$emit('update:modelValue', $event.target.checked)"
  >
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { isValid } from '@/jsHelper/forms';

export default defineComponent({
  name: 'CheckBox',
  props: {
    name: {
      type: String,
      required: true,
    },
    modelValue: {
      type: Boolean,
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
        type: 'CheckBox',
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
