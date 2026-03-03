.PHONY: test test-ui test-release fmt clippy check

test:
	cargo test

test-ui:
	xvfb-run -a cargo test

test-release:
	xvfb-run -a cargo test
	cd tests/ui_integration && xvfb-run -a python3 -m pytest -v

fmt:
	cargo +nightly fmt

clippy:
	cargo clippy -- -W clippy::pedantic

check: fmt clippy test
