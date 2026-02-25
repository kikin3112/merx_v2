```markdown
# ERP System Frontend Optimization - Project Guardrails

## ALWAYS
- Maintain backward compatibility with existing API endpoints during all refactoring phases
- Implement feature flags for all new real-time functionality to allow gradual rollout
- Use Zustand's immutability helpers (immer) for all state updates to prevent reactivity issues
- Implement comprehensive error boundaries around all virtualized components
- Maintain existing user roles and permissions structure during module consolidation
- Include loading states and skeleton screens for all data-intensive operations
- Implement proper TypeScript types for all new store structures and components
- Use cursor-based pagination for all list endpoints handling 500+ items
- Include proper loading states and optimistic updates for all real-time features
- Maintain existing URL structures and routing patterns during module consolidation
- Implement comprehensive logging and monitoring for all new real-time connections
- Use react-window or equivalent for all lists exceeding 100 items
- Include proper ARIA labels and keyboard navigation for all new components
- Implement proper error handling and fallback states for all SSE connections
- Maintain existing data validation rules during module consolidation
- Include proper testing for all new component interactions and state transitions

## NEVER
- Break existing user workflows during any refactoring or consolidation
- Remove any existing functionality without providing clear migration paths
- Mutate state directly in any store or component
- Implement real-time features without proper fallback mechanisms
- Consolidate modules without first analyzing user journey impact
- Remove existing API endpoints without maintaining backward compatibility
- Implement virtualization without proper loading states and error boundaries
- Break existing URL structures or routing patterns
- Remove existing user roles or permissions during consolidation
- Implement new features without proper accessibility considerations
- Break existing data validation or business logic rules
- Remove existing error handling without implementing proper replacements
- Implement real-time features without proper monitoring and alerting
- Break existing responsive design patterns during module consolidation
- Remove existing keyboard navigation support
- Implement new components without proper testing coverage

## SECURITY
- All real-time connections must use secure WebSockets (wss://) or authenticated SSE
- Implement proper rate limiting on all real-time endpoints
- Validate all data received through SSE connections before updating state
- Maintain existing authentication and authorization checks during module consolidation
- Implement proper CORS policies for all new real-time connections
- Sanitize all user inputs in unified forms to prevent injection attacks
- Maintain existing audit logging for all data modifications
- Implement proper session management for all real-time connections
- Validate all cursor-based pagination parameters to prevent data exposure
- Maintain existing data encryption standards for sensitive information
- Implement proper error handling to avoid information leakage
- Maintain existing security headers and policies during refactoring

## PERFORMANCE
- All virtualized lists must maintain 60fps scrolling performance
- Real-time updates must not block main thread or cause UI jank
- All new components must be optimized with React.memo where appropriate
- Cursor-based pagination queries must include proper database indexing
- All SSE connections must implement proper reconnection logic with
