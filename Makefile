.PHONY: start stop restart status logs content-studio video-studio install clean

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CONTENT_STUDIO_PORT ?= $(shell grep CONTENT_STUDIO_PORT .env 2>/dev/null | cut -d= -f2 || echo 5001)
VIDEO_STUDIO_PORT   ?= $(shell grep VIDEO_STUDIO_PORT .env 2>/dev/null | cut -d= -f2 || echo 5002)
LOG_DIR             := /tmp

# ---------------------------------------------------------------------------
# Start / Stop
# ---------------------------------------------------------------------------

## Start all studios
start: content-studio video-studio
	@echo ""
	@echo "All studios started."
	@echo "  Content Studio: http://localhost:$(CONTENT_STUDIO_PORT)"
	@echo "  Video Studio:   http://localhost:$(VIDEO_STUDIO_PORT)"
	@echo ""
	@echo "Run 'make logs' to tail logs, 'make stop' to shut down."

## Start content studio only
content-studio:
	@if lsof -i :$(CONTENT_STUDIO_PORT) -t > /dev/null 2>&1; then \
		echo "Content Studio already running on port $(CONTENT_STUDIO_PORT)"; \
	else \
		echo "Starting Content Studio on port $(CONTENT_STUDIO_PORT)..."; \
		nohup uv run content-studio > $(LOG_DIR)/content-studio.log 2>&1 & \
		echo "  PID: $$!"; \
		sleep 3; \
		if curl -sf http://localhost:$(CONTENT_STUDIO_PORT)/health > /dev/null 2>&1; then \
			echo "  Status: RUNNING"; \
		else \
			echo "  Status: STARTING (check 'make logs-content' if it fails)"; \
		fi; \
	fi

## Start video studio only
video-studio:
	@if lsof -i :$(VIDEO_STUDIO_PORT) -t > /dev/null 2>&1; then \
		echo "Video Studio already running on port $(VIDEO_STUDIO_PORT)"; \
	else \
		echo "Starting Video Studio on port $(VIDEO_STUDIO_PORT)..."; \
		nohup uv run video-studio > $(LOG_DIR)/video-studio.log 2>&1 & \
		echo "  PID: $$!"; \
		sleep 3; \
		if curl -sf http://localhost:$(VIDEO_STUDIO_PORT)/health > /dev/null 2>&1; then \
			echo "  Status: RUNNING"; \
		else \
			echo "  Status: STARTING (check 'make logs-video' if it fails)"; \
		fi; \
	fi

## Stop all studios
stop:
	@echo "Stopping all studios..."
	@for port in $(CONTENT_STUDIO_PORT) $(VIDEO_STUDIO_PORT); do \
		pids=$$(lsof -i :$$port -t 2>/dev/null); \
		if [ -n "$$pids" ]; then \
			echo "  Killing port $$port (PIDs: $$pids)"; \
			echo "$$pids" | xargs kill 2>/dev/null; \
		fi; \
	done
	@sleep 1
	@echo "All studios stopped."

## Restart all studios
restart: stop
	@sleep 1
	@$(MAKE) start

# ---------------------------------------------------------------------------
# Status / Logs
# ---------------------------------------------------------------------------

## Show status of all studios
status:
	@echo "=== Agent Factory Status ==="
	@echo ""
	@printf "  Content Studio (:%s): " "$(CONTENT_STUDIO_PORT)"
	@if curl -sf http://localhost:$(CONTENT_STUDIO_PORT)/health > /dev/null 2>&1; then \
		echo "RUNNING"; \
	else \
		echo "STOPPED"; \
	fi
	@printf "  Video Studio   (:%s): " "$(VIDEO_STUDIO_PORT)"
	@if curl -sf http://localhost:$(VIDEO_STUDIO_PORT)/health > /dev/null 2>&1; then \
		echo "RUNNING"; \
	else \
		echo "STOPPED"; \
	fi
	@echo ""

## Tail all logs
logs:
	@tail -f $(LOG_DIR)/content-studio.log $(LOG_DIR)/video-studio.log 2>/dev/null || echo "No log files found."

## Tail content studio logs
logs-content:
	@tail -f $(LOG_DIR)/content-studio.log 2>/dev/null || echo "No log file found."

## Tail video studio logs
logs-video:
	@tail -f $(LOG_DIR)/video-studio.log 2>/dev/null || echo "No log file found."

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

## Install dependencies
install:
	uv sync --all-packages

## Clean generated files and caches
clean:
	rm -rf generated/*.png generated/*.mp4 generated/*.jpg
	rm -rf data/*.db
	rm -rf __pycache__ packages/*/__pycache__ packages/*/*/__pycache__
	@echo "Cleaned generated files and caches."

## Show help
help:
	@echo "Agent Factory - Makefile Commands"
	@echo ""
	@echo "  make start          Start all studios (content + video)"
	@echo "  make stop           Stop all studios"
	@echo "  make restart        Restart all studios"
	@echo "  make status         Show running status"
	@echo ""
	@echo "  make content-studio Start content studio only"
	@echo "  make video-studio   Start video studio only"
	@echo ""
	@echo "  make logs           Tail all logs"
	@echo "  make logs-content   Tail content studio logs"
	@echo "  make logs-video     Tail video studio logs"
	@echo ""
	@echo "  make install        Install dependencies (uv sync)"
	@echo "  make clean          Remove generated files and caches"
