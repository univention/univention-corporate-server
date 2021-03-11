<template>
  <div
    v-if="(Object.keys(metaData).length > 0 && metaData.cookieBanner.show) && getCookies"
    :class="fadeOutClass"
    class="cookie-banner"
  >
    <transition name="fade">
      <div
        class="cookie-banner__container"
        role="dialog"
        aria-labelledby=""
      >
        <div class="cookie-banner__title-bar">
          <span
            class="cookie-banner__title"
            role="heading"
            level="1"
          >
            {{ $localized(metaData.cookieBanner.title) }}
          </span>
        </div>
        <div class="cookie-banner__pane-content">
          <div class="cookie-banner__container-widget">
            <div class="cookie-banner__text">
              {{ $localized(metaData.cookieBanner.text) }}
            </div>
          </div>
        </div>
        <div class="cookie-banner__action-bar">
          <span
            class="cookie-banner__button portal-reset"
            role="presentation"
          >
            <portal-button
              button-label="ACCEPT"
              class="cookie-banner__button-text"
              @click.stop="setCookies()"
            />
          </span>
        </div>
      </div>
    </transition>

    <teleport to="body">
      <div
        :class="fadeOutClass"
        class="cookie-banner__blackout"
      >
        <div
          class="cookie-banner__blackout-content"
          tabindex="-1"
        />
      </div>
    </teleport>
  </div>
</template>

<script lang="ts">
import { Options, Vue } from 'vue-class-component';
import { mapGetters } from 'vuex';

import PortalButton from '@/components/globals/PortalButton.vue';
import HeaderButton from '@/components/navigation/HeaderButton.vue';
import Translate from '@/i18n/Translate.vue';

import { setCookie, getCookie } from '@/jsHelper/cookieHelper';

@Options({
  name: 'CookieBanner',
  components: {
    PortalButton,
    HeaderButton,
    Translate,
  },
  data() {
    return {
      showCookieBanner: false,
      fadeOutClass: '',
    };
  },
  computed: {
    ...mapGetters({
      metaData: 'meta/getMeta',
    }),
    getCookies() {
      if (getCookie(this.cookieName()) === '') {
        this.showCookieBanner = true;
      }
      return this.showCookieBanner;
    },
  },
  methods: {
    cookieName() {
      return this.metaData.cookieBanner.cookie || 'univentionCookieSettingsAcceptedxx';
    },
    setCookies() {
      const cookieValue = 'do-not-change-me';

      setCookie(this.cookieName(), cookieValue);
      this.dismissCookieBanner();
    },
    dismissCookieBanner() {
      this.fadeOutClass = 'cookie-banner__fade-out';
      setTimeout(() => {
        this.showCookieBanner = !this.showCookieBanner;
      }, 600);
    },
  },
})
export default class CookieBanner extends Vue {}
</script>

<style lang="stylus">
.cookie-banner
  position: fixed
  top: auto
  left: 0
  bottom: 0
  right: 0
  z-index: $zindex-10
  width: 100%
  max-width: 100%
  box-shadow: 0px 14px 45px rgb(0 0 0 / 25%), 0px 10px 18px rgb(0 0 0 / 22%)
  border-radius: var(--border-radius-container)
  background-color: var(--color-grey0)
  &__title-bar
    padding: 30px 30px 5px 30px
    display: flex
    align-items: center
  &__pane-content
    padding: 5px 30px 40px 30px
    border-bottom: 1px solid rgba(255, 255, 255, 0.16)
  &__button
    box-shadow: var(--box-shadow)
    margin: 0
    font-size: var(--button-font-size)
    border-radius: var(--button-border-radius)
    background-color: var(--button-text-bgc)
    padding: 8px 30px
    line-height: 30px
    transition: background-color 250ms
    &:hover,
    &:focus
      background-color: var(--button-text-bgc-overlay-hover)
      cursor: pointer
    &:active
      background-color: var(--button-text-bgc-overlay-active)
  &__button-close
    margin-left: auto
  &__button-text
    text-transform: uppercase
    color: var(--font-color-contrast-high)
    font-family: 'Open Sans', sans-serif
    font-size: 16px
    font-weight: 600
  &__action-bar
    background-color: var(--color-grey0)
    display: flex
    justify-content: space-between
    border-top: thin solid var(--color-grey8)
    padding: 8px 24px
  &__fade-out
    visibility: hidden;
    opacity: 0;
    transition: visibility 0s .3s, opacity .5s linear;

  &__blackout
    position: fixed
    top: 0
    left: 0
    z-index: $zindex-9
    background: #5a5a5a
    opacity: 0.5
    min-height: 100vh
    width: 100vw
  &__blackout-content
    display: block
</style>
