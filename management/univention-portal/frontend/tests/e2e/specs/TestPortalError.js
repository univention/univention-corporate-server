/*
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
*/

import 'cypress-axe';

const loadOtherFiles = () => {
  cy.intercept('GET', 'meta.json', { fixture: 'meta.json' });
  cy.intercept('GET', 'de.json', { fixture: 'de.json' });
  cy.intercept('GET', 'languages.json', { fixture: 'languages.json' });
  cy.setCookie('univentionCookieSettingsAccepted', 'doesthisneedavalue');
};

describe('Test Portal Error Components', () => {
  it('Shows Error if portal.json is not returned successfully', () => {
    cy.intercept('GET', 'portal.json', { statusCode: 500 });
    loadOtherFiles();
    cy.visit('/');

    const errorContainer = cy.get('.portal-error');

    errorContainer.should('be.visible');
    errorContainer.should((container) => {
      // make sure the first contains text "sorry"
      expect(container.first()).to.contain('Sorry');
    });
  });

  it('Shows Not found component if given url is false', () => {
    cy.intercept('GET', 'portal.json', { fixture: 'portal_logged_in.json' });
    loadOtherFiles();

    // invalid url after "#"
    cy.visit('/#/gibberish');

    const errorContainer = cy.get('.portal-error');
    errorContainer.should('be.visible');
    errorContainer.should((container) => {
      // make sure the first contains text "sorry"
      expect(container.first()).to.contain('Page not found');
    });
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
