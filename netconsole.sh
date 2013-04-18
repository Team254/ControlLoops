#!/bin/bash

# READLINE is nicer, but it dies when given lots of output
socat UDP4-RECV:6666,reuseaddr!!UDP4-SENDTO:10.2.54.2:6668 STDIO
