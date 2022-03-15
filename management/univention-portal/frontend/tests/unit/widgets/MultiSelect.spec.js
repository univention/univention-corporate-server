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
import MultiSelect from '@/components/widgets/MultiSelect.vue';
import Vuex from 'vuex';

const fullModelValue = ['cn=Backup Join,cn=groups,dc=dev,dc=upx,dc=mydemoenv,dc=net', 'cn=Computers,cn=groups,dc=dev,dc=upx,dc=mydemoenv,dc=net', 'cn=DC Backup Hosts,cn=groups,dc=dev,dc=upx,dc=mydemoenv,dc=net', 'cn=DC Slave Hosts,cn=groups,dc=dev,dc=upx,dc=mydemoenv,dc=net'];

const multiSelectProps = {
  label: 'multi select',
  modelValue: [],
  name: '',
};

let wrapper;

beforeEach(async () => {
  wrapper = await mount(MultiSelect, {
    propsData: multiSelectProps,
  });
});

afterEach(() => {
  wrapper.unmount();
});

describe('MultiInput.vue', () => {
  test('if Button with label "Add entry" exists', async () => {
    const addMoreButton = await wrapper.find('[data-test="multi-select-add-more-button"]');

    expect(addMoreButton.text()).toContain('Add more');
    expect(addMoreButton.text()).toContain('Add Groups');
    expect(addMoreButton.find('[aria-hidden="true"]').exists()).toBeTruthy();
    expect(addMoreButton.find('[class="sr-only sr-only-mobile"]').exists()).toBeTruthy();
  });

  test('if Button with label "Remove" exists', async () => {
    const removeButton = await wrapper.find('[data-test="multi-select-remove-button"]');

    expect(removeButton.text()).toContain('Remove');
    expect(removeButton.text()).toContain('Remove selection');
    expect(removeButton.find('[aria-hidden="true"]').exists()).toBeTruthy();
    expect(removeButton.find('[class="sr-only sr-only-mobile"]').exists()).toBeTruthy();
  });

  test('if elementsSelected returns true when this.selection.length greater than 0', async () => {
    expect(wrapper.vm.elementsSelected).toBe(false);

    // setup props and trigger selection to expect elementsSelected to Be true
    await wrapper.setProps({ modelValue: fullModelValue });

    const firstCheckbox = await wrapper.find('input');
    await firstCheckbox.trigger('change');
    expect(wrapper.vm.elementsSelected).toBe(true);
  });

  test('if toggleSelection is called correctly', async () => {
    const toggleSelectionSpy = jest.spyOn(wrapper.vm, 'toggleSelection');
    await wrapper.setProps({ modelValue: fullModelValue });
    await wrapper.vm.$nextTick();

    const firstCheckbox = await wrapper.find('input');
    await firstCheckbox.trigger('change');

    expect(toggleSelectionSpy).toHaveBeenCalled();
    expect(wrapper.vm.selection).toEqual(['cn=Backup Join,cn=groups,dc=dev,dc=upx,dc=mydemoenv,dc=net']);
  });

  test('if dnToLabel returning string correctly', async () => {
    // hoping that the dn-string, will always have the same structure :)
    // recieves argument
    const dnToLabelSelectionSpy = jest.spyOn(wrapper.vm, 'dnToLabel');
    const newModelvalue = ['cn=Backup Join,xxxxx'];
    wrapper.setProps({ modelValue: newModelvalue });
    await wrapper.vm.$nextTick();

    // retrieves the desired label
    const label = await wrapper.find('[data-test="multi-select-checkbox-span"]');
    expect(label.text()).toBe('Backup Join');
    expect(dnToLabelSelectionSpy).toHaveBeenCalledWith(newModelvalue[0]);
  });

  test.skip('if add is working as expected', async () => {
    wrapper.unmount();
    const store = new Vuex.Store({
      modules: {
        modal: {
          namespaced: true,
        },
        activity: {
          namespaced: true,
        },
      },
    });

    wrapper = await mount(MultiSelect, {
      propsData: multiSelectProps,
      global: {
        plugins: [store],
      },
    });

    store.dispatch = jest.fn().mockImplementation(() => Promise.resolve());

    wrapper.setProps({ modelValue: fullModelValue });
    const addButton = await wrapper.find('[data-test="multi-select-add-more-button"]');

    await addButton.trigger('click');

    await wrapper.vm.$nextTick();

    expect(store.dispatch).toHaveBeenCalledWith('modal/setShowModalPromise', {
      level: 2,
      name: 'AddObjects',
      props: {
        alreadyAdded: wrapper.vm.modelValue,
      },
      stubborn: true,
    });

    expect(store.dispatch).toHaveBeenCalledWith('modal/hideAndClearModal', 2);

    //  // update:modelValue is called with newValues
    // // dispatch setMessage is called
  });

  test('if remove is working as expected', async () => {
    wrapper.unmount();
    const store = new Vuex.Store({
      modules: {
        activity: {
          namespaced: true,
        },
      },
    });

    wrapper = await mount(MultiSelect, {
      propsData: {
        label: 'multi select',
        modelValue: fullModelValue,
        name: '',
      },
      global: {
        plugins: [store],
      },
    });

    store.dispatch = jest.fn();

    const firstCheckbox = wrapper.find('[data-test="multi-select-checkbox-span"]');
    const removeButton = await wrapper.find('[data-test="multi-select-remove-button"]');
    await firstCheckbox.trigger('click');
    await removeButton.trigger('click');

    await wrapper.vm.$nextTick();
    expect(wrapper.emitted()).toHaveProperty('update:modelValue');
    expect(store.dispatch).toHaveBeenCalledWith('activity/setMessage', 'Removed selection');
  });
});
