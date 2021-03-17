<template>
  <div
    v-show="isActive"
    class="portal-iframe"
  >
    <span
      class="portal-iframe__status"
    />
    <iframe
      :src="link"
      title="Embedded Page"
      class="portal-iframe__iframe"
      allow="geolocation; microphone; camera; midi; encrypted-media"
    />
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
  name: 'PortalIframe',
  props: {
    link: {
      type: String,
      required: true,
    },
    isActive: {
      type: Boolean,
      default: false,
    },
  },
});
</script>

<style lang="stylus">
.portal-iframe
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;

  &__iframe
    position: relative;
    border: none;
    width: 100%;
    height: 100%;

</style>
