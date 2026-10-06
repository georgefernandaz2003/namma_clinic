import { vi } from 'vitest';

// Basic DOM polyfills for jsdom environment
if (typeof window !== 'undefined') {
  window.scrollTo = vi.fn();
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation(query => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });

  // Polyfill ResizeObserver for Recharts ResponsiveContainer
  class ResizeObserverMock {
    observe = vi.fn();
    unobserve = vi.fn();
    disconnect = vi.fn();
  }
  window.ResizeObserver = ResizeObserverMock as unknown as typeof ResizeObserver;

  // Polyfill getBoundingClientRect for jsdom measurements
  Element.prototype.getBoundingClientRect = () => ({
    width: 800,
    height: 300,
    top: 0,
    left: 0,
    bottom: 300,
    right: 800,
    x: 0,
    y: 0,
    toJSON: () => {},
  });
}
