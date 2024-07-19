# etherlink-watchtower
Watchtower for Etherlink Bridge withdrawal operations

## Local Setup
### Prerequisites
- Install [Poetry](https://python-poetry.org/docs/#installation) if not already installed.

### Installation
1. Install dependencies:
```bash
poetry install
```

2. Copy and configure environment variables:
```bash
cp .env.dist .env
source .env
```

3. Start the watchtower:
```bash
poetry run python app.py
```

## Docker Setup
### Build Docker Image
```bash
docker build -t etherlink-watchtower .
```

### Run Docker Container
```bash
docker run -d --name watchtower --env-file .env.dist etherlink-watchtower
```
