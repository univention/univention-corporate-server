<!--
Copyright 2021 Univention GmbH

https://www.univention.de/

All rights reserved.

The source code of this program is made available
under the terms of the GNU Affero General Public License version 3
(GNU AGPL V3) as published by the Free Software Foundation.

Binary versions of this program provided by Univention to you as
well as other copyrighted, protected or trademarked materials like
Logos, graphics, fonts, specific documentations and configurations,
cryptographic keys etc. are subject to a license agreement between
you and Univention and not subject to the GNU AGPL V3.

In the case you use this program under the terms of the GNU AGPL V3,
the program is provided in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public
License with the Debian GNU/Linux or Univention distribution in file
/usr/share/common-licenses/AGPL-3; if not, see
<https://www.gnu.org/licenses/>.
-->
<template>
  <div>
    <transition name="fade">
      <slot
        v-if="bubbleStateStandalone || bubbleStateNewBubble"
        name="bubble-standalone"
      />
    </transition>

    <slot
      name="bubble-embedded"
    />
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

export default defineComponent({
  name: 'NotificationBubble',
  computed: {
    ...mapGetters({
      bubbleState: 'notificationBubble/bubbleState',
      bubbleStateStandalone: 'notificationBubble/bubbleStateStandalone',
      bubbleStateNewBubble: 'notificationBubble/bubbleStateNewBubble',
    }),
  },
});
</script>

<style lang="stylus">
.notification-bubble
  &__container
    background-color: rgba(0,0,0,0.4);
    backdrop-filter: blur(2rem);
    border-radius: var(--border-radius-notification);

  &__standalone
    position: absolute
    right: 2rem
    top: 0.8rem
    margin: 0;
    max-width: 20rem;

  &__embedded
    position: relative

// animation
.fade-enter-active,
.fade-leave-active
  transition: opacity .5s

.fade-enter,
.fade-leave-to
  opacity: 0
</style>
