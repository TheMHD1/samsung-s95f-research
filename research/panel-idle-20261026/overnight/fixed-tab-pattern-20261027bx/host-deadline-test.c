/* Host-only Linux POSIX timer semantic test. This is not an ARM target helper. */
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
int main(void) {
    pid_t child = fork();
    if (child < 0) return 10;
    if (child == 0) {
        timer_t timer;
        struct sigevent ev = {0};
        ev.sigev_notify = SIGEV_SIGNAL;
        ev.sigev_signo = SIGKILL;
        if (timer_create(CLOCK_MONOTONIC, &ev, &timer) != 0) _exit(11);
        struct itimerspec interval = {0};
        interval.it_value.tv_nsec = 100000000;
        if (timer_settime(timer, 0, &interval, NULL) != 0) _exit(12);
        for (;;) pause();
    }
    int status;
    while (waitpid(child, &status, 0) < 0) if (errno != EINTR) return 13;
    if (!WIFSIGNALED(status) || WTERMSIG(status) != SIGKILL) return 14;
    puts("{\"host_posix_timer_sigkill\":true,\"target_abi_tested\":false,\"target_operations\":0}");
    return 0;
}
