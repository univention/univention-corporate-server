/**
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
* */

import { mount } from '@vue/test-utils';

import PortalToolTip from '@/components/PortalToolTip.vue';
import IconButton from '@/components/globals/IconButton.vue';

import Vuex from 'vuex';
import activity from '@/store/modules/activity';

const tooltipProps = {
  title: 'Tooltip title',
  description: 'Tooltip description',
  ariaId: 'ariaID',
  position: {
    bottom: 305,
    left: 48,
    right: 176,
    top: 140,
    x: 48,
    y: 140,
  },
  isMobile: false,
  linkType: {
    label: 'embedded',
    icon: 'layout',
  },
};

const state = { tooltip: tooltipProps, hoverOnToolip: false, tooltipID: 1 };

const store = new Vuex.Store({
  modules: {
    tooltip: {
      state,
      namespaced: true,
    },
    activity: {
      getters: activity.getters,
      namespaced: true,
    },
  },
});

store.dispatch = jest.fn();

let wrapper;

beforeEach(async () => {
  wrapper = await mount(PortalToolTip, {
    propsData: tooltipProps,
    children: [IconButton],
    global: {
      plugins: [store],
    },
    attachTo: document.body,
  });
});

afterEach(() => {
  wrapper.unmount();
});

describe('PortalToolTip.vue', () => {
  test('check if description tag contains description text"', async () => {
    const descriptionTag = wrapper.find('[data-test="portal-tooltip-description"]');
    expect(descriptionTag.text()).toBe(wrapper.vm.description);
  });

  test('check if data: calculatedPosition is set with position props', async () => {
    const expectedObject = {
      left: wrapper.vm.position.left,
      bottom: wrapper.vm.position.bottom,
      zone: 'REGULAR',
    };
    expect(wrapper.vm.calculatedPosition).toEqual(expectedObject);
  });

  test('CLOSE_TOOLTIP computed property is set and passed for icon', async () => {
    const closeToolTipIcon = wrapper.find('[data-test="portal-tooltip-close-icon"]');
    expect(closeToolTipIcon.attributes('aria-label')).toBe(wrapper.vm.CLOSE_TOOLTIP);
  });

  test('tooltipPosition', async () => {
    // tooltip position is calculated only for desktop
    expect(wrapper.vm.tooltipPosition).toBe(`left:${wrapper.vm.calculatedPosition.left}px;`);
  });

  test('arrowPosition is set for regular placement', async () => {
    const tooltipArrow = wrapper.find('[data-test="portal-tooltip-arrow"]');
    expect(tooltipArrow.attributes('style')).toBe('top: -2rem; left: 0.2rem;');
  });

  test('keepTooltip is working on mouseover', async () => {
    const toolTip = wrapper.find('[data-test="portal-tooltip"]');
    toolTip.trigger('mouseenter');
    await wrapper.vm.$nextTick();
    expect(store.dispatch).toHaveBeenCalledWith('tooltip/setHoverOnTooltip', true);
  });

  test('closeToolTip is triggered on mouseleave', async () => {
    const toolTip = wrapper.find('[data-test="portal-tooltip"]');
    toolTip.trigger('mouseleave');
    await wrapper.vm.$nextTick();
    expect(store.dispatch).toHaveBeenCalledWith('tooltip/setHoverOnTooltip', false);
    expect(store.dispatch).toHaveBeenCalledWith('tooltip/unsetTooltip');
  });
});
