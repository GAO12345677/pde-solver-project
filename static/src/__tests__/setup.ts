import '@testing-library/jest-dom';
import { vi } from 'vitest';

Object.defineProperty(globalThis.HTMLCanvasElement.prototype, 'getContext', {
  value: vi.fn(() => ({})),
});

if (!globalThis.URL.createObjectURL) {
  globalThis.URL.createObjectURL = vi.fn(() => 'blob:mock-url');
}

if (!globalThis.URL.revokeObjectURL) {
  globalThis.URL.revokeObjectURL = vi.fn();
}

if (!globalThis.ResizeObserver) {
  globalThis.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as typeof ResizeObserver;
}
