# TypeScript / React — Refactoring Checklist

Covers **TypeScript / React Frontend** (`.ts`, `.tsx`, `.js`, `.jsx` files) and **Frontend Testing** (`.test.ts`, `.test.tsx`, `.spec.ts`, `.spec.tsx` files).

---

## TypeScript / React Frontend

### Component Design

- Single responsibility: one component, one purpose.
- Composition over prop drilling. Use context or state management for deeply shared data.
- Handle all UI states: loading, error, empty, and success.
- Extract reusable logic into custom hooks.

### TypeScript Strictness

- No `any`. Use `unknown` and narrow with type guards.
- Use discriminated unions for variant types.
- Define explicit types for component props — avoid inline object types in complex cases.
- Use `readonly` for props and state that should not be mutated.
- Use `as const` for literal types.

### React Hooks

- Correct dependency arrays in `useEffect`, `useCallback`, `useMemo`.
- Always provide cleanup functions in `useEffect` when subscribing to events or timers.
- Use `useCallback` and `useMemo` only when there is a measured performance benefit — not by default.
- Extract complex hook logic into custom hooks with clear names.

### State Management

- Keep state as local as possible. Lift only when necessary.
- Derive values from state instead of storing computed values.
- Avoid redundant state that can be calculated from other state.
- Use refs for values that should not trigger re-renders.

### Accessibility

- Semantic HTML elements (`button`, `nav`, `main`, `article`) over generic `div`/`span`.
- ARIA attributes where semantic HTML is insufficient.
- Keyboard navigation: all interactive elements must be keyboard-accessible.
- Focus management for modals, drawers, and dynamic content.

### Performance

- Lazy load routes and heavy components with `React.lazy()` and `Suspense`.
- Virtualize long lists (react-window, react-virtualized, tanstack-virtual).
- Avoid unnecessary re-renders: memoize expensive computations, not everything.
- Code-split by route to reduce initial bundle size.

### Documentation

- JSDoc comments on all exported functions, hooks, and component props.
- Document non-obvious prop behavior and side effects.

---

## Frontend Testing

### Framework and Structure

- Use the project's existing test framework (Jest, Vitest, Playwright, Cypress).
- Co-locate test files with source files (`Component.test.tsx` next to `Component.tsx`).
- Use `describe`/`it` blocks for organized test structure.

### React Testing Library

- Test behavior, not implementation. Query by role, label, or text — not by class or test ID.
- Use `userEvent` over `fireEvent` for realistic interaction simulation.
- Test accessibility: verify ARIA roles, labels, and keyboard navigation.
- Avoid testing internal component state — test what the user sees.

### Coverage

- Test all user interactions: clicks, typing, form submission, navigation.
- Test error states: API failures, validation errors, edge cases.
- Test loading states and empty states.
- Snapshot tests only for stable, visual-regression-sensitive components.
