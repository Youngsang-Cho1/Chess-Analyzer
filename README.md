# Chess Analyzer ♟️

A Python-based tool to analyze your Chess.com games, built with **Docker**, **PostgreSQL**, and **Python**.

## Features
- Fetches game archives from Chess.com API.
- Stores game data in a local PostgreSQL database.
- (Planned) Parses PGNs for opening analysis and blunder detection.

## Setup

### Prerequisites
- Docker & Docker Compose installed.

### Installation
1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd chess-analyzer
    ```
2.  Create a `.env` file (based on `.env.example` if available) with your DB credentials:
    ```env
    POSTGRES_USER=your_user
    POSTGRES_PASSWORD=your_password
    POSTGRES_DB=chess_db
    ```
3.  Run the application:
    ```bash
    docker-compose up --build -d
    ```

## Usage
- Run the main script:
    ```bash
    docker-compose run --rm chess-analyzer python main.py
    ```

## Tech Stack
- **Language**: Python 3.11+
- **Database**: PostgreSQL 15
- **Infrastructure**: Docker Compose
