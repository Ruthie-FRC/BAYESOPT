// Copyright (c) 2025 FRC 6328
// http://github.com/Mechanical-Advantage
//
// Use of this source code is governed by an MIT-style
// license that can be found in the LICENSE file at
// the root directory of this project.

package frc.robot.generic.util;

import frc.robot.Constants;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import java.util.function.Consumer;
import java.util.function.DoubleSupplier;
import org.littletonrobotics.junction.networktables.LoggedNetworkNumber;

/**
 * Class for a tunable number. Gets value from dashboard in tuning mode, returns default if not or
 * value not in dashboard.
 */
public class LoggedTunableNumber implements DoubleSupplier {
  private static final String tableKey = "/Tuning";

  private final double defaultValue;
  private final LoggedNetworkNumber dashboardNumber;
  private final Map<Integer, Double> lastHasChangedValues = new HashMap<>();

  /**
   * Create a new LoggedTunableNumber with the default value
   *
   * @param dashboardKey Key on dashboard
   * @param defaultValue Default value
   */
  public LoggedTunableNumber(String dashboardKey, double defaultValue) {
    this.defaultValue = defaultValue;
    if (Constants.tuningMode) {
      String key = tableKey + "/" + dashboardKey;
      dashboardNumber = new LoggedNetworkNumber(key, defaultValue);
    } else {
      dashboardNumber = null;
    }
  }

  /**
   * Get the current value, from dashboard if available and in tuning mode.
   *
   * @return The current value
   */
  public double get() {
    return Constants.tuningMode ? dashboardNumber.get() : defaultValue;
  }

  /**
   * Checks whether the number has changed since our last check
   *
   * @param id Unique identifier for the caller to avoid conflicts when shared between multiple
   *     objects. Recommended approach is to pass the result of "hashCode()" This will be less
   *     optimised than using {@link #hasChanged(Object)}
   * @return True if the number has changed since the last time this method was called, false
   *     otherwise.
   */
  public boolean hasChanged(int id) {
    if (!Constants.tuningMode) return false;
    return hasChangedUnchecked(id);
  }

  /**
   * Checks whether the number has changed since our last check
   *
   * @param id Object to get hashcode() of (if in tuning mode). This should just be {@code this}
   *     This is used as a unique identifier for the caller to avoid conflicts when shared between
   *     multiple objects.
   * @return True if the number has changed since the last time this method was called, false if not
   *     in tuning mode or otherwise.
   */
  public boolean hasChanged(Object id) {
    if (!Constants.tuningMode) return false;
    return hasChangedUnchecked(id.hashCode());
  }

  /**
   * Checks whether the number has changed since our last check
   *
   * @param id Unique identifier for the caller to avoid conflicts when shared between multiple
   *     objects. Likely "hashCode()"
   * @return whether the number has changed
   */
  private boolean hasChangedUnchecked(int id) {
    double currentValue = get();
    Double lastValue = lastHasChangedValues.get(id);
    if (lastValue == null || currentValue != lastValue) {
      lastHasChangedValues.put(id, currentValue);
      return true;
    }
    return false;
  }

  /**
   * Runs action if any of the tunableNumbers have changed
   *
   * @param id Unique identifier for the caller to avoid conflicts when shared between multiple *
   *     objects. Recommended approach is to pass the result of "hashCode()". This will be less
   *     optimised than using {@link #ifChanged(Object, Consumer, LoggedTunableNumber...)}
   * @param action Callback to run when any of the tunable numbers have changed. Access tunable
   *     numbers in order inputted in method
   * @param tunableNumbers All tunable numbers to check
   */
  public static void ifChanged(
      int id, Consumer<double[]> action, LoggedTunableNumber... tunableNumbers) {
    if (!Constants.tuningMode) return;
    ifChangedUnchecked(id, action, tunableNumbers);
  }

  /**
   * Runs action if any of the tunableNumbers have changed
   *
   * @param id Object to get hashcode() of (if in tuning mode). This should just be {@code this}
   *     This is used as a unique identifier for the caller to avoid conflicts when shared between
   *     multiple objects.
   * @param action Callback to run when any of the tunable numbers have changed. Access tunable
   *     numbers in order inputted in method
   * @param tunableNumbers All tunable numbers to check
   */
  public static void ifChanged(
      Object id, Consumer<double[]> action, LoggedTunableNumber... tunableNumbers) {
    if (!Constants.tuningMode) return;
    ifChangedUnchecked(id.hashCode(), action, tunableNumbers);
  }

  private static void ifChangedUnchecked(
      int id, Consumer<double[]> action, LoggedTunableNumber... tunableNumbers) {
    if (Arrays.stream(tunableNumbers).anyMatch(tunableNumber -> tunableNumber.hasChanged(id))) {
      action.accept(Arrays.stream(tunableNumbers).mapToDouble(LoggedTunableNumber::get).toArray());
    }
  }

  /** Runs action if any of the tunableNumbers have changed */
  public static void ifChanged(int id, Runnable action, LoggedTunableNumber... tunableNumbers) {
    ifChanged(id, values -> action.run(), tunableNumbers);
  }

  @Override
  public double getAsDouble() {
    return get();
  }
}
