.PHONY: build install clean test

BINARY_NAME := ophiron-sdk
BIN_DIR := bin

build:
	@echo "Building SDK..."
	@mkdir -p $(BIN_DIR)
	go build -o $(BIN_DIR)/$(BINARY_NAME) .
	@echo "Build complete: $(BIN_DIR)/$(BINARY_NAME)"

install: build
	@echo "Installing SDK..."
	sudo cp $(BIN_DIR)/$(BINARY_NAME) /usr/local/bin/
	@echo "SDK installed to /usr/local/bin/$(BINARY_NAME)"

clean:
	@echo "Cleaning..."
	rm -rf $(BIN_DIR)
	@echo "Clean complete"

test:
	@echo "Running SDK tests..."
	go test ./...

deps:
	@echo "Installing dependencies..."
	go mod download
	go mod tidy

