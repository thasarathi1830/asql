// @vitest-environment jsdom
import { describe, it, expect } from 'vitest';
import React from 'react';
import { renderToString } from 'react-dom/server';
import App from './App';

describe('PHANTOM Frontend Suite', () => {
  it('renders application landing page and navigation without error', () => {
    window.history.pushState({}, 'Test', '/');
    const html = renderToString(<App />);
    expect(html).toContain('PHANTOM');
    expect(html).toContain('Launch Command Center');
  });

  it('renders onboarding new customer route', () => {
    window.history.pushState({}, 'Test', '/customers/new');
    const html = renderToString(<App />);
    expect(html).toContain('New Customer Onboarding');
  });

  it('renders transactions route with real-time screener', () => {
    window.history.pushState({}, 'Test', '/transactions');
    const html = renderToString(<App />);
    expect(html).toContain('Pre-Transaction Real-Time AML Screener');
  });
});
