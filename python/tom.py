package com.team254.frc2013;

import com.team254.lib.control.StateSpaceGains;

public class WheelGains {
  static public StateSpaceGains[] getGains() {
    return new StateSpaceGains[] {
        new StateSpaceGains(
            new double[] {...},  // A
            new double[] {...},  // B
            new double[] {...},  // C
            new double[] {...},  // D
            new double[] {...},  // L
            new double[] {...},  // K
            new double[] {...},  // Umax
            new double[] {...}),  // Umin
        };
  }
}
