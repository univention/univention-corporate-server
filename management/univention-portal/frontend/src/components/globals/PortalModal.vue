<template>
  <teleport to="body">
    <div
      class="portal-modal"
      :class="{ 'portal-modal--isVisible': isActive }"
      @click="clickHandler"
    >
      <slot ref="TEST" />
    </div>
  </teleport>
</template>

<script lang="ts">
import { Options, Vue } from 'vue-class-component';

@Options({
  name: 'PortalModal',
  props: {
    isActive: {
      type: Boolean,
      required: true,
    },
  },

  // Todo: move to vuex store, avoid emits
  emits: ['click'],
  methods: {
    clickHandler(evt) {
      if (evt.target.classList.contains('portal-modal')) {
        this.$emit('click');
      }
    },
  },
})

export default class PortalModal extends Vue {}
</script>

<style lang="stylus">
.portal-modal
    width: 100%;
    position: fixed;
    height: 100%;
    top: 0;
    right: 0;
    bottom: 0;
    left: 0;
    z-index: -999

    &--isVisible
      z-index: 0
      background-color: rgba(51, 51, 49, 0.5);
      display: flex
      align-items: center
      justify-content: center

      &> *
        position: relative
        z-index: 1
</style>
