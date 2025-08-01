# Notion Client Project

A Python project for interacting with the Notion API using the official notion-client library.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file from the example:
   ```bash
   copy .env.example .env
   ```

3. Add your Notion integration token to the `.env` file

4. Run the application:
   ```bash
   python main.py
   ```

## Getting a Notion Integration Token

1. Go to https://www.notion.so/my-integrations
2. Create a new integration
3. Copy the "Internal Integration Token"
4. Share your Notion pages/databases with the integration

## Usage

The main.py file demonstrates basic usage of the Notion client to list databases.