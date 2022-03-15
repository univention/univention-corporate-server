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

import PortalSearch from '@/components/search/PortalSearch.vue';
import navigation from '@/store/modules/navigation';
import Vuex from 'vuex';

test('Portalsearch', async () => {
  // to check focus, we need to attach to an actual document, normally we don't do this
  const div = document.createElement('div');
  div.id = 'root';
  document.body.appendChild(div);

  /*
    After some trials and tribulations I currently believe it's a good idea to mock the store where
    possible and ensure the desired interaction with the store, i.e. pressing button x triggers dispatch y.
    The store should be tested separately
     */

  const state = {
    activeButton: 'search',
  };

  const actions = {
    setActiveButton: jest.fn(),
  };

  const store = new Vuex.Store({
    modules: {
      navigation: {
        state,
        actions,
        getters: navigation.getters,
        namespaced: true,
      },
    },
  });
  store.dispatch = jest.fn();

  const wrapper = await mount(PortalSearch, {
    global: {
      plugins: [store],
    },
    attachTo: '#root',
  });

  const input = await wrapper.find('.portal-search__input');
  // ensure that input is focussed after mounting
  expect(input.element).toBe(document.activeElement);

  // ensure search is triggered by typing
  await input.setValue('univention');
  expect(store.dispatch).toHaveBeenLastCalledWith('activity/setMessage', '0 search results');

  // ensure that after hitting escape the activebutton is set to ''
  await input.trigger('keyup.esc');
  expect(store.dispatch).toHaveBeenLastCalledWith('navigation/setActiveButton', '');

  // ensure searchquery is empty on unmount
  wrapper.unmount();
  expect(store.dispatch).toHaveBeenLastCalledWith('search/setSearchQuery', '');
});
