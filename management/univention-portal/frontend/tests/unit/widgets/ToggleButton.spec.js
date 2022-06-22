/**
  Copyright 2021-2022 Univention GmbH

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
* */

import { mount } from '@vue/test-utils';

import ToggleButton from '@/components/widgets/ToggleButton.vue';
import IconButton from '@/components/globals/IconButton.vue';
import Vuex from 'vuex';
import activity from '@/store/modules/activity';

const store = new Vuex.Store({
  modules: {
    activity: {
      getters: activity.getters,
      namespaced: true,
    },
  },
});

const toggleLabelProp = {
  initial: 'Display as List',
  toggled: 'Display as Grid',
};
const toggleIconProp = {
  initial: 'list',
  toggled: 'grid',
};

describe('ToggleButton Component', () => {
  test('Button displays initial Icon and text', async () => {
    const wrapper = await mount(ToggleButton, {
      propsData: {
        toggleLabels: toggleLabelProp,
        toggleIcons: toggleIconProp,
      },
      children: [IconButton],
      global: {
        plugins: [store],
      },
    });

    const button = await wrapper.find('[data-test="toggle-button"]');
    const svgChild = await wrapper.find('use');
    expect(button.attributes('aria-label')).toBe('Display as List');
    expect(svgChild.attributes('href')).toBe('feather-sprite.svg#list');

    await button.trigger('click');

    expect(button.attributes('aria-label')).toBe('Display as Grid');
    expect(svgChild.attributes('href')).toBe('feather-sprite.svg#grid');
    wrapper.unmount();
  });
});
