# Requirements Document

## Introduction

This feature restructures the existing YouTube-to-Notion integration codebase to improve modularity, testability, and maintainability. The current implementation has grown organically with functionality concentrated in single files/classes, making it difficult to read, test, and extend. This restructuring introduces clear abstractions and component separation while maintaining full operational compatibility.

## Requirements

### Requirement 1

**User Story:** As a developer, I want the application to have clear component boundaries with single responsibilities, so that I can easily understand, modify, and test individual parts of the system.

#### Acceptance Criteria

1. WHEN the system processes a YouTube video THEN it SHALL use separate components for analysis, metadata extraction, markdown enrichment, and storage
2. WHEN a component is modified THEN it SHALL not require changes to unrelated components
3. WHEN the system runs THEN it SHALL maintain the same external behavior and CLI interface as before restructuring
4. WHEN components interact THEN they SHALL use well-defined interfaces and abstractions
5. WHEN new functionality is added THEN it SHALL be possible to extend components without modifying existing code

### Requirement 2

**User Story:** As a developer, I want pluggable summary implementations, so that I can introduce different AI providers or expand summary logic without affecting the rest of the process.

#### Acceptance Criteria

1. WHEN the system generates summaries THEN it SHALL use a SummaryWriter abstraction that can be implemented by different providers
2. WHEN a new AI provider is added THEN it SHALL implement the SummaryWriter interface without changing other components
3. WHEN summary logic is enhanced THEN it SHALL not require modifications to video processing or storage components
4. WHEN conversation logging is needed THEN it SHALL be handled by the summary implementation, not the main process
5. WHEN the system runs THEN it SHALL support switching between different summary implementations via configuration

### Requirement 3

**User Story:** As a developer, I want pluggable storage backends, so that I can replace Notion with other databases or add multiple storage targets without changing the core processing logic.

#### Acceptance Criteria

1. WHEN the system stores processed content THEN it SHALL use a Storage abstraction that can be implemented by different backends
2. WHEN a new storage backend is added THEN it SHALL implement the Storage interface without changing processing components
3. WHEN Notion-specific logic is needed THEN it SHALL be contained within the Notion storage implementation
4. WHEN markdown conversion is required THEN it SHALL be handled by the storage implementation that needs it
5. WHEN the system runs THEN it SHALL support different storage backends via configuration

### Requirement 4

**User Story:** As a developer, I want separate unit and integration test suites, so that I can run fast component tests during development and comprehensive integration tests for validation.

#### Acceptance Criteria

1. WHEN unit tests run THEN they SHALL not connect to external services, write logs, or perform I/O operations
2. WHEN unit tests run THEN they SHALL complete in under 10 seconds total
3. WHEN integration tests run THEN they SHALL use a separate test Notion database "YT Summaries [TEST]"
4. WHEN integration tests run THEN they SHALL use `.env-test` configuration file and never use the actual `.env` file
5. WHEN integration tests run THEN they SHALL verify that all components work together correctly
6. WHEN tests are executed THEN unit and integration tests SHALL be clearly separated and runnable independently

### Requirement 5

**User Story:** As a developer, I want the application to remain fully operational after each restructuring step, so that I can deploy incremental improvements without breaking existing functionality.

#### Acceptance Criteria

1. WHEN any restructuring step is completed THEN the application SHALL maintain all existing CLI functionality
2. WHEN components are refactored THEN all existing tests SHALL continue to pass
3. WHEN new abstractions are introduced THEN they SHALL be backward compatible with existing usage
4. WHEN the restructuring is complete THEN the application SHALL have identical external behavior to the original
5. WHEN intermediate steps are deployed THEN they SHALL not break existing user workflows

### Requirement 6

**User Story:** As a developer, I want in-memory mocking capabilities for the main processing flow, so that I can test the complete workflow without external dependencies.

#### Acceptance Criteria

1. WHEN unit tests run THEN they SHALL use in-memory implementations of Storage and SummaryWriter abstractions
2. WHEN the processing flow is tested THEN it SHALL be possible to mock all external dependencies
3. WHEN abstractions are implemented THEN they SHALL support both real and mock implementations
4. WHEN tests verify the flow THEN they SHALL test component interactions without I/O operations
5. WHEN mocks are used THEN they SHALL provide realistic behavior for testing edge cases