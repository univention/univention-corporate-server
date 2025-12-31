/*
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
*/

import 'cypress-axe';

describe('Test Tabs', () => {
  it('shows Iframe Tabs', () => {
    // TODO: Same origin html fake for linktarget tests
    cy.intercept('GET', 'portal.json', { fixture: 'portal_test_tabs.json' });
    cy.intercept('GET', 'meta.json', { fixture: 'meta.json' });
    cy.intercept('GET', 'de.json', { fixture: 'de.json' });
    cy.intercept('GET', 'languages.json', { fixture: 'languages.json' });
    cy.setCookie('univentionCookieSettingsAccepted', 'doesthisneedavalue');
    cy.visit('/');
    // first click results to first tab and first Iframe (first element in array)
    cy.get('.portal-category .portal-tile').first()
      .click();
    cy.get('#iframe-1').should('be.visible');
    // click to portal
    cy.get('.portal-title__portal-name').click();
    cy.get('#portalCategories').should('be.visible');
    cy.get('iframe').should('not.be.visible');
    // click to first tab expects to have visible iframe
    cy.get('#headerTab__1').click();
    cy.get('iframe').should('be.visible');
    // go back to portal to open second tab
    cy.get('.portal-title__portal-name').click();
    cy.get('#portalCategories').should('be.visible');
    cy.get('.portal-category .portal-tile').last()
      .click();
    cy.get('iframe').should('be.visible');
    // now we have two tabs and can switch between them
    cy.get('[data-test="header-tabs"]').children()
      .should('have.length', 2);
    cy.get('#headerTab__1').click();
    cy.get('#iframe-1').should('be.visible');
    cy.get('iframe').should('be.focused');
    // closing last tab of two
    cy.get('#headerTab__2').click();
    cy.get('#iframe-2').should('be.visible');
    cy.get('[data-test="close-tab-2"]').click();
    cy.get('#portalCategories').should('be.visible');
    cy.get('[data-test="header-tabs"]').children()
      .should('have.length', 1);
    cy.get('[data-test="portal-iframes"]').children()
      .should('have.length', 1);
    // closing remaining tab
    cy.get('[data-test="close-tab-1"]').click();
    cy.get('#portalCategories').should('be.visible');
    cy.get('[data-test="header-tabs"]').children()
      .should('have.length', 0);
    cy.get('[data-test="portal-iframes"]').children()
      .should('have.length', 0);
  });
  it('test store', () => {
    cy.readFile('public/data/portal.json').then((portal) => {
      portal.entries[0].linkTarget = 'embedded';
      cy.intercept('GET', 'portal.json', portal);
      cy.intercept('GET', 'meta.json', { fixture: 'meta.json' });
      cy.intercept('GET', 'de.json', { fixture: 'de.json' });
      cy.intercept('GET', 'languages.json', { fixture: 'languages.json' });
      cy.setCookie('univentionCookieSettingsAccepted', 'doesthisneedavalue');
      cy.visit('/');
      const getStore = () => cy.window().its('store');
      getStore().its('state')
        .should('have.any.keys', ['activeTabIndex', 'tabs', 'scrollPosition']);
      // open Tab to see if it correctly in store
      getStore().its('state')
        .its('tabs')
        .its('tabs')
        .should('have.length', 0);
      cy.get('.portal-category .portal-tile').last()
        .click();
      cy.get('#iframe-1').should('be.visible');
      getStore().its('state')
        .its('tabs')
        .its('tabs')
        .should('have.length', 1);
    });
  });

  it('test scroll position', () => {
    cy.readFile('public/data/portal.json').then((portal) => {
      portal.entries[0].linkTarget = 'embedded';
      cy.intercept('GET', 'portal.json', portal);
      cy.intercept('GET', 'meta.json', { fixture: 'meta.json' });
      cy.intercept('GET', 'de.json', { fixture: 'de.json' });
      cy.intercept('GET', 'languages.json', { fixture: 'languages.json' });
      cy.setCookie('univentionCookieSettingsAccepted', 'doesthisneedavalue');

      cy.viewport('iphone-x', 'landscape');
      cy.visit('/');
      const getStore = () => cy.window().its('store');
      getStore().its('state')
        .should('have.any.keys', ['activeTabIndex', 'tabs', 'scrollPosition']);
      // open Tab to see if it correctly in store
      getStore().its('state')
        .its('tabs')
        .its('scrollPosition')
        .should('eq', 0);
      cy.get('.portal-category .portal-tile').last()
        .click();
      // cy.get('#iframe-1').should('be.visible');
      getStore().its('state')
        .its('tabs')
        .its('scrollPosition')
        .should('be.greaterThan', 0);
    });
  });
  /* eslint-disable jest/expect-expect */
  it('A11y Test', () => {
    cy.injectAxe();
    cy.checkA11y('[data-test="header-tabs"]',
      {
        runOnly: {
          type: 'tag',
          values: ['wcag21aa'],
        },
      },
      cy.terminalLog, {
        skipFailures: false,
      });
  });

  /* eslint-enable jest/expect-expect */
});
