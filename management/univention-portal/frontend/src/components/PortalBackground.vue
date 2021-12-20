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
  <div
    class="portal__background"
    :style="backgroundImageStyle"
  >
  <Particles
    id="particles"
    :particlesInit="particlesInit"
    :particlesLoaded="particlesLoaded"
    :options="particlesConfig"
  />
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

export default defineComponent({
  name: 'PortalBackground',
  computed: {
    ...mapGetters({ portal: 'portalData/getPortal' }),
    backgroundImageStyle(): string {
      if (!this.portal.portal.background) {
        return 'background-image: none';
      }
      return `background-image: url('${this.portal.portal.background}')`;
    },
  },
  setup() {
    const particlesConfig = {
      particles: {
        number: {
          value: 55,
          density: {
            enable: true,
            value_area: 670,
          },
        },
        fpsLimit: 60,
        color: {
          value: '#617f1f',
        },
        shape: {
          type: 'circle',
          stroke: {
            width: 1,
            color: '#617f1f',
          },
          polygon: {
            nb_sides: 5,
          },
          image: {
            src: 'img/github.svg',
            width: 100,
            height: 100,
          },
        },
        opacity: {
          value: 0.5,
          random: true,
          anim: {
            enable: true,
            speed: 0.4,
            opacity_min: 0.3,
            sync: false,
          },
        },
        size: {
          value: 2,
          random: true,
          anim: {
            enable: true,
            speed: 3,
            size_min: 2,
            sync: false,
          },
        },
        line_linked: {
          enable: true,
          distance: 150,
          color: '#617f1f',
          opacity: 0.33,
          width: 1,
        },
        move: {
          enable: true,
          speed: 0.9,
          direction: 'none',
          random: true,
          straight: false,
          out_mode: 'bounce',
          bounce: false,
          attract: {
            enable: false,
            rotatex: 600,
            rotatey: 1200,
          },
        },
      },
      interactivity: {
        detect_on: 'window',
        events: {
          onhover: {
            enable: true,
            mode: 'bubble',
          },
          onclick: {
            enable: false,
            mode: 'push',
          },
          resize: true,
        },
        modes: {
          bubble: {
            distance: 120,
            size: 5,
            duration: 10,
            opacity: 1,
            speed: 1,
          },
          remove: {
            particles_nb: 2,
          },
        },
      },
      retina_detect: false,
    };
    return { particlesConfig };
  },
});
</script>

<style lang="stylus">
.portal__background {
  position: fixed;
  z-index: $zindex-0;
  top: var(--portal-header-height);
  left: 0;
  right: 0;
  bottom: 0;
  background-position: top center;
  background-size: cover;
  background-repeat: no-repeat;
}
</style>
