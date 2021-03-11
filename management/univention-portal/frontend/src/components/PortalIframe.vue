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
import { Options, Vue } from 'vue-class-component';

@Options({
  name: 'PortalIframe',
  props: {
    link: String,
    isActive: {
      type: Boolean,
      default: false,
    },
  },
})
export default class PortalTile extends Vue {}
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
