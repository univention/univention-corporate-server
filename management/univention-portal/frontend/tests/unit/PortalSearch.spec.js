import {shallowMount} from '@vue/test-utils'
import PortalSearch from '@/components/search/PortalSearch'
import Vuex from 'vuex'

test('Test Portalsearch', async () => {

    // to check focus, we need to attach to an actual document, normally we don't do this
    const div = document.createElement('div')
    div.id = 'root'
    document.body.appendChild(div)

    /*
    After some trials and tribulations I currently believe it's a good idea to mock the store where
    possible and ensure the desired interaction with the store, i.e. pressing button x triggers dispatch y.
    The store should be tested separately
     */

    const store = new Vuex.Store()
    store.dispatch = jest.fn()

    const wrapper = await shallowMount(PortalSearch, {
        global: {
            plugins: [store]
        },
        attachTo: "#root"
    })

    const input = await wrapper.find('.portal-search__input')
    // ensure that input is focussed after mounting
    expect(input.element).toBe(document.activeElement)

    // ensure search is triggered by typing
    await input.setValue('univention')
    expect(store.dispatch).toHaveBeenLastCalledWith('search/setSearchQuery', 'univention')

    // ensure that after hitting escape the activebutton is set to ''
    await input.trigger('keyup.esc');
    expect(store.dispatch).toHaveBeenLastCalledWith('navigation/setActiveButton', '')

    // ensure searchquery is empty on unmount
    wrapper.unmount()
    expect(store.dispatch).toHaveBeenLastCalledWith("search/setSearchQuery", "")
});
