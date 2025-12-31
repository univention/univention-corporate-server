<!--
SPDX-FileCopyrightText: 2022-2026 Univention GmbH
SPDX-License-Identifier: AGPL-3.0-only
-->
<template>
  <div
    class="standbyCircle"
  >
    <svg
      viewBox="0 0 100 100"
      xmlns="http://www.w3.org/2000/svg"
    >
      <circle
        cx="50"
        cy="50"
        r="45"
      />
    </svg>
  </div>
</template>

<style lang="stylus">
.standbyCircle
  width: 2rem
  height: 2rem
  display: flex
  color: var(--bgc-loading-circle)

  svg
    animation: 2s linear infinite svg-animation
    width: 100%
    height: 100%

  circle
    animation: 1.4s ease-in-out infinite both circle-animation
    display: block
    fill: transparent
    stroke: currentColor
    stroke-linecap: round
    stroke-dasharray: 283
    stroke-dashoffset: 280
    stroke-width: 10px
    transform-origin: 50% 50%

@keyframes svg-animation {
  0% {
    transform: rotateZ(0deg);
  }
  100% {
    transform: rotateZ(360deg)
  }
}

@keyframes circle-animation {
  0%,
  25% {
    stroke-dashoffset: 280;
    transform: rotate(0);
  }

  50%,
  75% {
    stroke-dashoffset: 75;
    transform: rotate(45deg);
  }

  100% {
    stroke-dashoffset: 280;
    transform: rotate(360deg);
  }
}
</style>
