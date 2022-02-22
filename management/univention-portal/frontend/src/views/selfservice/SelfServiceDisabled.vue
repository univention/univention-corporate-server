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
  <div class="self-service-disabled">
    <h1 class="self-service-disabled__title">
      {{ TITLE }}
    </h1>
    <p class="self-service-disabled__text">
      {{ TEXT }}
    </p>
  </div>
</template>
<script lang="ts">
import { defineComponent } from 'vue';
import _ from '@/jsHelper/translate';

export default defineComponent({
  name: 'SelfServiceDisabled',
  computed: {
    TITLE(): string {
      return _('This service is disabled');
    },
    TEXT(): string {
      return _('If you have problems using the self service instance, please contact your system administrator.');
    },
  },
  mounted() {
    this.$store.dispatch('activity/setMessage', `${this.TITLE}. ${this.TEXT}`);
  },
});
</script>
<style lang="stylus">
.self-service-disabled
  position: relative
  display: flex
  flex-direction: column

  @media $mqSmartphone
    margin-left: 1em

  &__title
    margin-bottom: 0
</style>
