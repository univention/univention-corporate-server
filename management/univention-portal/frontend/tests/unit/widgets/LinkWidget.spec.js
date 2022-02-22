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

import LinkWidget from '@/components/widgets/LinkWidget.vue';
import Vuex from 'vuex';
import activity from '@/store/modules/activity';

const modelValueLinkWidget = [{ locale: 'en_US', value: 'http://10.200.4.60/owncloud' }, { locale: 'en_US', value: 'https://master60.intranet.portal.de/owncloud' }, { locale: 'en_US', value: 'www.duckduckgo.com' }];

const linkWidgetProps = {
  extraLabel: 'Links',
  modelValue: modelValueLinkWidget,
  name: 'links',
};

let wrapper;

const mockedLocaleGetter = {
  getAvailableLocales: () => ['en_US', 'de_DE'],
  getLocale: () => 'en_US',
};

const store = new Vuex.Store({
  modules: {
    locale: {
      getters: mockedLocaleGetter,
      namespaced: true,
    },
    activity: {
      getters: activity.getters,
      namespaced: true,
    },
  },
});

beforeEach(async () => {
  wrapper = await mount(LinkWidget, {
    propsData: linkWidgetProps,
    global: {
      plugins: [store],
    },
    attachTo: document.body,
  });
});

afterEach(() => {
  wrapper.unmount();
});

describe('LinkWidget.vue', () => {
  test('if Remove-Button exists and is working as expected', async () => {
    const removeButton = await wrapper.find('[data-test="link-widget-remove-button-0"]');

    // Since we have no text we we still want to know if the right icon exists.
    expect(removeButton.find('[xlink:href="feather-sprite.svg#trash"]').exists()).toBeTruthy();

    expect(removeButton.attributes('aria-label')).toBe('Link 1: Remove');

    // each Button removes it's own line, so after clicking on the button we expect,
    // that modelvalue is reduced by one
    const amountOfValues = wrapper.vm.modelValueData.length;

    await removeButton.trigger('click');
    await wrapper.vm.$nextTick();
    expect(wrapper.emitted()).toHaveProperty('update:modelValue');
    expect(wrapper.vm.modelValueData.length).toBe(amountOfValues - 1);
  });

  test('if "add link"-button is working as expected', async () => {
    const addFieldButton = wrapper.find('[data-test="add-field"]');
    const amountOfValues = wrapper.vm.modelValueData.length;
    expect(addFieldButton.text()).toContain('Add link');
    await addFieldButton.trigger('click');
    expect(wrapper.vm.modelValueData.length).toBe(amountOfValues + 1);
  });

  test('if each Select-Element in a row has an individual aria label', () => {
    const listOfSelectElements = wrapper.findAll('select');
    listOfSelectElements.forEach((element, index) => {
      expect(element.attributes('aria-label')).toBe(`${wrapper.vm.LINK(index)} Select locale for Link`);
    });
  });

  test('if each Input-Element in a row has an individual aria label', () => {
    const listOfInputElements = wrapper.findAll('input');
    listOfInputElements.forEach((element, index) => {
      expect(element.attributes('aria-label')).toBe(`${wrapper.vm.LINK(index)} insert valid Link`);
    });
  });

  test('if each Remove-button in a row has an individual aria label', () => {
    const listOfRemoveButtonElements = wrapper.findAll('.link-widget__remove button');
    listOfRemoveButtonElements.forEach((element, index) => {
      expect(element.attributes('aria-label')).toBe(`${wrapper.vm.LINK(index)} ${wrapper.vm.REMOVE}`);
    });
  });

  test('if computed properties actually return desired values', () => {
    expect(wrapper.vm.REMOVE).toBe('Remove');
    expect(wrapper.vm.LINK(0)).toBe('Link 1:');
    expect(wrapper.vm.localeSelect(0)).toBe('Link 1: Select locale for Link');
    expect(wrapper.vm.linkInput(0)).toBe('Link 1: insert valid Link');
  });

  test('if option in select has correct data', () => {
    const availableLocales = wrapper.vm.locales;
    const select = wrapper.find('select');
    const options = select.findAll('option');
    options.forEach((option, index) => {
      expect(option.text()).toBe(availableLocales[index]);
    });
  });

  test('if select has necessary attributes', async () => {
    const allSelects = wrapper.findAll('select');
    allSelects.forEach((select, index) => {
      expect(select.attributes('aria-label')).toBe(wrapper.vm.localeSelect(index));
    });
  });

  test('if input has correct attributes', () => {
    const allTextInputs = wrapper.findAll('input');
    allTextInputs.forEach((input, index) => {
      expect(input.attributes('aria-label')).toBe(wrapper.vm.linkInput(index));
      expect(input.attributes('autocomplete')).toBe('off');
      if (index === 0) {
        expect(input.attributes('name')).toBe(wrapper.vm.name);
      } else {
        expect(input.attributes('name')).toBe(`${wrapper.vm.name}-${index}`);
      }
    });
  });

  test('if created remodels the given modalValueObject', () => {
    const expectedArray = modelValueLinkWidget;
    expectedArray.push({ locale: 'en_US', value: '' });
    expect(wrapper.vm.modelValueData).toEqual(expectedArray);
  });
});
