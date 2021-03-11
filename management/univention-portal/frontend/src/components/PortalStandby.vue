<template>
  <div class="portal-standby">
    <div class="portal-standby__lds-ring">
      <div class="portal-standby__ring-item" />
      <div class="portal-standby__ring-item" />
      <div class="portal-standby__ring-item" />
      <div class="portal-standby__ring-item" />
    </div>
  </div>
</template>

<style scoped lang="stylus">
.portal-standby
  position: absolute
  top: 0
  left: 0
  background-color: rgba(30, 30, 29, 0.7)
  width: 100%
  height: 100%

  &__lds-ring
    display: inline-block
    position: relative
    width: 80px
    height: 80px
    top: 45%
    left: 45%

  &__ring-item
    box-sizing: border-box
    display: block
    position: absolute
    width: 64px
    height: 64px
    margin: 8px
    border: 8px solid transparent
    border-radius: 50%
    animation: lds-ring 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite
    border-color: var(--color-grey40) transparent transparent transparent

    &:nth-child(1)
      animation-delay: -0.45s

    &:nth-child(2)
      animation-delay: -0.3s

    &:nth-child(3)
      animation-delay: -0.15s

@keyframes lds-ring
  0%
    transform: rotate(0deg)
  100%
    transform: rotate(360deg)
</style>
