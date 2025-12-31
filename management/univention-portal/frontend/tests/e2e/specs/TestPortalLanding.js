/*
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
*/

import 'cypress-axe';

beforeEach(() => {
  cy.clearCookie('univentionCookieSettingsAccepted');
  cy.setCookie('UMCLang', 'de_DE');
  // stuff selenium can't do #1: mock requests / responses
  cy.intercept('GET', 'portal.json', { fixture: 'portal_logged_out.json' });
  // cy.intercept('GET', 'portal/portal.json', { fixture: 'portal_logged_in.json' });
  cy.intercept('GET', 'meta.json', { fixture: 'meta.json' });
  cy.intercept('GET', 'de.json', { fixture: 'de.json' });
  cy.intercept('GET', 'languages.json', { fixture: 'languages.json' });
  cy.visit('/');
  cy.get('main.cookie-banner + footer button.button--primary').click();
});

describe('Test Portal Landing', () => {
  it('General loading of tiles and menu', () => {
    cy.contains('h2', 'Verwaltung');
    // Tiles?
    cy.get('.portal-tile__name').contains('span', 'Univention Blog');

    cy.get('[data-test="navigationbutton"]').click();
    cy.wait(500);
    cy.get('.portal-sidenavigation__link').contains('Anmelden');
    cy.contains('Zertifikate');
    cy.contains('Apps');
    cy.contains('Hilfe');
  });

  it('Mouseover is working', () => {
    // Mouseover tooltip?
    cy.get('.portal-category .portal-tile').first()
      .trigger('mouseenter');
    cy.get('[data-test="portal-tooltip"]').contains('Cloud Lösung');
    cy.get('.portal-category .portal-tile').first()
      .trigger('mouseleave');
    cy.get('[data-test="portal-tooltip"]').should('not.exist');
  });
  it('Headerbuttons become green', () => {
    // Buttons, check if they become green
    const searchbutton = cy.get('[data-test="searchbutton"]');
    searchbutton.should('not.have.class', 'header-button--is-active');
    searchbutton.click();
    searchbutton.should('have.class', 'header-button--is-active');

    const bellbutton = cy.get('[data-test="bellbutton"]');
    bellbutton.should('not.have.class', 'header-button--is-active');
    bellbutton.click();
    bellbutton.should('have.class', 'header-button--is-active');

    const menubutton = cy.get('[data-test="navigationbutton"]');
    menubutton.should('not.have.class', 'header-button--is-active');
    menubutton.click();
    menubutton.should('have.class', 'header-button--is-active');
    cy.get('.modal-wrapper--isVisible').click();
  });
  it('Cookie should exist', () => {
    cy.getCookie('univentionCookieSettingsAccepted').should('exist');
  });
  it('General a11y test', () => {
    cy.injectAxe();
    cy.checkA11y('body',
      {
        runOnly: {
          type: 'tag',
          values: ['wcag21aa'],
        },
      },
      cy.terminalLog, {
        skipFailures: true,
      });
  });
});
