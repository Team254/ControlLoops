#!/bin/bash
#
# Updates the wrist controller.

./python/wrist.py wrist/wrist_motor_plant.h \
    wrist/wrist_motor_plant.cc \
    wrist/unaugmented_wrist_motor_plant.h \
    wrist/unaugmented_wrist_motor_plant.cc
