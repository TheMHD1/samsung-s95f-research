CC ?= cc
CFLAGS = -std=c11 -Wall -Wextra -Werror -Wpedantic -O1 -g
SANITIZERS = -fsanitize=address,undefined -fno-omit-frame-pointer

.PHONY: check clean
check: host-test
	./host-test
	python3 offline_validate.py
	python3 -O offline_validate.py

host-test: test_host.c swu_prototype.c swu_prototype.h
	$(CC) $(CFLAGS) $(SANITIZERS) test_host.c -o $@

clean:
	rm -f host-test
