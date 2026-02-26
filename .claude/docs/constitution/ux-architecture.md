## Overview

The ERP system is a complex enterprise software that integrates financial data precision, operational efficiency, and real-time responsiveness. The architecture addresses critical front-end inconsistencies including dashboard update failures, inventory visualization issues, and fragmented user workflows. These are not merely aesthetic problems but structural failures that compromise strategic decision-making and regulatory compliance, particularly for Colombian electronic invoicing requirements under DIAN supervision.

## Components

**Dashboard Module**: Real-time billing dashboard that displays pending invoices and financial metrics. Originally implemented with traditional HTTP request-response model, causing latency between server events and user interface updates.

**Product Management Module**: Product catalog interface that lacks proper detail visibility and total count display. Users cannot see comprehensive product information or understand the full scope of their catalog.

**Inventory Management Module**: Multi-location inventory system suffering from pagination inconsistencies and incomplete data visualization. Users experience missing inventory records and cannot view hierarchical inventory details across different warehouses.

**State Management Layer**: Zustand-based global state management that requires normalization and immutability patterns to prevent reactivity-blocking mutations and ensure consistent data across components.

**Real-time Communication**: Server-Sent Events (SSE) implementation for pushing updates from server to client, replacing inefficient polling mechanisms for billing status changes and inventory updates.

**Virtualization Layer**: React-window integration for handling large datasets (100k+ rows) by rendering only visible items in viewport, dramatically improving memory usage and interface fluidity.

## Data Flow

Data flows through a normalized state architecture where each entity (products, invoices, inventory) maintains a single source of truth. When a billing event occurs, the server pushes updates via SSE to the dashboard store, which propagates changes to all subscribed components. Product and inventory data flows through cursor-based pagination to ensure consistent record visibility despite concurrent modifications. The virtualization layer intercepts list rendering requests, calculating visible items based on scroll position and rendering only those elements while maintaining the illusion of a full dataset.

## Key Decisions

**Server-Sent Events over WebSockets**: Chose SSE for dashboard updates because the information flow is predominantly server-to-client (billing status changes), making SSE simpler to implement over existing HTTP infrastructure with native reconnection handling. WebSockets were rejected as they introduce unnecessary complexity for unidirectional data flow scenarios.

**Cursor-based Pagination over Offset Pagination**: Implemented cursor pagination to solve the inconsistency problem where new records inserted at the top of result sets would shift existing records and cause users to miss or duplicate entries. Cursor pagination ensures users always see a consistent, complete view of their inventory regardless of concurrent modifications.

**Unified Module Architecture**: Decided to consolidate related functionality into single modules (product + inventory) rather than maintaining fragmented separate modules. This eliminates context switching, reduces navigation friction, and creates natural workflows where users can complete entire processes without leaving the context of their current task.
