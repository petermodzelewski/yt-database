# Requirements Document

## Introduction

This feature adds a web-based user interface mode to the YouTube-to-Notion integration application. The UI provides a visual queue management system with three columns (To Do, In Progress, Done) for tracking video processing status in real-time. Users can add YouTube URLs to a processing queue and monitor progress through an intuitive web interface that resembles YouTube's visual design.

## Requirements

### Requirement 1

**User Story:** As a user, I want to start the application in UI mode using a `--ui` flag, so that I can access a web-based interface for managing video processing.

#### Acceptance Criteria

1. WHEN the user runs the command with `--ui` flag THEN the system SHALL start a web server backend
2. WHEN the web server starts THEN the system SHALL automatically open a web browser to the UI interface
3. WHEN the UI mode is active THEN the system SHALL serve a webpage with YouTube-like visual styling
4. IF the user provides `--ui` flag THEN the system SHALL NOT process videos from command line arguments

### Requirement 2

**User Story:** As a user, I want to see a three-column layout (To Do, In Progress, Done), so that I can visually track the status of all video processing tasks.

#### Acceptance Criteria

1. WHEN the UI loads THEN the system SHALL display three distinct columns labeled "To Do", "In Progress", and "Done"
2. WHEN a URL is added to queue THEN the system SHALL display it in the "To Do" column
3. WHEN processing begins THEN the system SHALL move the URL from "To Do" to "In Progress" column
4. WHEN processing completes THEN the system SHALL move the URL from "In Progress" to "Done" column
5. WHEN displaying URLs THEN the system SHALL show video thumbnails extracted from the YouTube URL

### Requirement 3

**User Story:** As a user, I want to add YouTube URLs to the processing queue through the web interface, so that I can queue multiple videos for processing without using command line.

#### Acceptance Criteria

1. WHEN the user clicks the "+" button next to "To Do" column THEN the system SHALL display an input popup
2. WHEN the user enters a YouTube URL in the input THEN the system SHALL validate the URL format
3. WHEN a valid URL is submitted THEN the system SHALL add it to the "To Do" queue
4. WHEN an invalid URL is submitted THEN the system SHALL display an error message
5. WHEN the URL is added THEN the system SHALL close the input popup and refresh the "To Do" column

### Requirement 4

**User Story:** As a user, I want to see real-time status updates for videos being processed, so that I can monitor progress without refreshing the page.

#### Acceptance Criteria

1. WHEN a video is being processed THEN the system SHALL display the current processing phase (metadata extraction, AI summary generation, Notion upload)
2. WHEN processing a chunked video THEN the system SHALL display which chunk is currently being processed (e.g., "Processing chunk 2/4")
3. WHEN status changes occur THEN the system SHALL update the UI automatically without page refresh
4. WHEN multiple videos are in queue THEN the system SHALL process them sequentially and update status for each
5. WHEN processing fails THEN the system SHALL display error status and move the URL to appropriate column

### Requirement 5

**User Story:** As a user, I want to view chat logs for completed videos, so that I can review the AI conversation and processing details.

#### Acceptance Criteria

1. WHEN a video is in the "Done" column THEN the system SHALL display an eye button next to the URL
2. WHEN the user clicks the eye button THEN the system SHALL open a popup displaying the chat log
3. WHEN a video was processed in chunks THEN the system SHALL display additional numbered eye buttons for each chunk
4. WHEN the user clicks a chunk eye button THEN the system SHALL display the specific chunk's chat log
5. WHEN displaying chat logs THEN the system SHALL format them in a readable manner with proper styling

### Requirement 6

**User Story:** As a user, I want the backend to continue processing videos from the queue while serving the web interface, so that I can have a seamless experience.

#### Acceptance Criteria

1. WHEN the web server starts THEN the system SHALL initialize a video processing queue
2. WHEN URLs are added to queue THEN the system SHALL process them using existing VideoProcessor logic
3. WHEN processing videos THEN the system SHALL maintain all existing functionality (AI summaries, Notion integration, chat logging)
4. WHEN processing completes THEN the system SHALL update the web interface with results
5. WHEN the server shuts down THEN the system SHALL gracefully complete any in-progress video processing

### Requirement 7

**User Story:** As a user, I want the web interface to have YouTube-like visual appeal, so that the interface feels familiar and professional.

#### Acceptance Criteria

1. WHEN the UI loads THEN the system SHALL use a color scheme and typography similar to YouTube
2. WHEN displaying video thumbnails THEN the system SHALL extract and show actual YouTube video thumbnails
3. WHEN showing video information THEN the system SHALL display title, duration, and channel information when available
4. WHEN styling the interface THEN the system SHALL use modern web design principles with responsive layout
5. WHEN displaying status information THEN the system SHALL use clear visual indicators (progress bars, status badges, icons)

### Requirement 8

**User Story:** As a user, I want real-time updates without page refreshes, so that I can monitor progress continuously without manual intervention.

#### Acceptance Criteria

1. WHEN status changes occur THEN the system SHALL push updates to the web interface using WebSocket or Server-Sent Events
2. WHEN new URLs are added THEN the system SHALL immediately reflect them in the UI
3. WHEN processing status changes THEN the system SHALL update the relevant column and status information
4. WHEN videos move between columns THEN the system SHALL animate the transitions smoothly
5. WHEN connection is lost THEN the system SHALL attempt to reconnect and sync the current state

### Requirement 9

**User Story:** As a developer, I want the web UI components to be well-tested and properly separated, so that the code maintains high quality and follows existing project standards.

#### Acceptance Criteria

1. WHEN implementing web UI components THEN the system SHALL separate functionality into well-sized, single-responsibility components
2. WHEN creating components THEN the system SHALL implement abstract interfaces for testability
3. WHEN writing unit tests THEN the system SHALL follow existing project standards (fast execution, no external API calls, mock implementations)
4. WHEN testing web components THEN the system SHALL use dependency injection and mock implementations from test fixtures
5. WHEN testing real-time features THEN the system SHALL mock WebSocket/SSE connections and simulate events
6. WHEN running tests THEN the system SHALL complete all web UI tests within the existing fast test suite timeframe
7. WHEN implementing the web server THEN the system SHALL use the existing ComponentFactory pattern for dependency injection

### Requirement 10

**User Story:** As a developer, I want to avoid code duplication between CLI and UI modes, so that both modes share the same core processing logic and maintain consistency.

#### Acceptance Criteria

1. WHEN implementing UI mode THEN the system SHALL use a shared queue system for both CLI batch processing and web UI processing
2. WHEN processing videos in UI mode THEN the system SHALL reuse existing VideoProcessor, ComponentFactory, and all processing components
3. WHEN implementing queue functionality THEN the system SHALL create a reusable queue component that works for both CLI and UI modes
4. WHEN running CLI batch mode THEN the system SHALL use the same queue system internally as the UI mode
5. WHEN testing queue functionality THEN the system SHALL write comprehensive unit tests for queue operations (add, remove, status updates, error handling)
6. WHEN queue state changes THEN the system SHALL provide observable events that both CLI and UI can consume
7. WHEN implementing queue persistence THEN the system SHALL ensure queue state can be maintained across application restarts if needed

### Requirement 11

**User Story:** As a product owner, I want the README documentation to be updated after implementation, so that users understand how to use the new UI mode feature.

#### Acceptance Criteria

1. WHEN the UI mode is implemented THEN the system SHALL update the README with `--ui` flag documentation
2. WHEN documenting UI mode THEN the system SHALL include screenshots or descriptions of the three-column interface
3. WHEN updating README THEN the system SHALL add setup instructions for any new dependencies (web server, frontend assets)
4. WHEN documenting features THEN the system SHALL explain how to add URLs, monitor progress, and view chat logs
5. WHEN updating CLI documentation THEN the system SHALL maintain existing command examples while adding UI mode examples
6. WHEN documenting architecture THEN the system SHALL update any architecture diagrams to include web UI components