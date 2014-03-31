#!/bin/bash

# READLINE is nicer, but it dies when given lots of output
socat UDP4-RECV:6666,reuseaddr!!UDP4-SENDTO:127.0.0.1:6668 STDIO
