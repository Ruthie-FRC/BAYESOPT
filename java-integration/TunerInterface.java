// Copyright (c) FIRST and other WPILib contributors.
// Open Source Software; you can modify and/or share it under the terms of
// the WPILib BSD license file in the root directory of this project.

package frc.robot.util;

import edu.wpi.first.networktables.BooleanSubscriber;
import edu.wpi.first.networktables.DoubleSubscriber;
import edu.wpi.first.networktables.NetworkTable;
import edu.wpi.first.networktables.NetworkTableInstance;
import edu.wpi.first.networktables.StringSubscriber;
import edu.wpi.first.wpilibj.Timer;

/**
 * Helper class for interfacing with the BayesOpt Python tuner.
 *
 * <p>This class provides methods to check tuner status and read dashboard controls set by the
 * tuner. Use this class to check if shooting is allowed based on tuner interlocks.
 *
 * <p><b>Location:</b> Copy to {@code src/main/java/frc/robot/util/TunerInterface.java}
 */
public final class TunerInterface {
  private static TunerInterface s_instance;

  private final NetworkTableInstance m_ntInstance;

  // Subscribers for tuner status
  private final DoubleSubscriber m_heartbeatSub;
  private final BooleanSubscriber m_tunerEnabledSub;
  private final StringSubscriber m_tunerStatusSub;
  private final StringSubscriber m_currentCoefficientSub;
  private final DoubleSubscriber m_shotCountSub;
  private final DoubleSubscriber m_shotThresholdSub;

  // Interlock subscribers
  private final BooleanSubscriber m_requireShotLoggedSub;
  private final BooleanSubscriber m_requireCoeffUpdatedSub;
  private final BooleanSubscriber m_shotLoggedSub;
  private final BooleanSubscriber m_coeffUpdatedSub;

  // Fine-tuning subscribers
  private final BooleanSubscriber m_fineTuningEnabledSub;
  private final StringSubscriber m_targetBiasSub;
  private final DoubleSubscriber m_biasAmountSub;

  /**
   * Gets the singleton instance of TunerInterface.
   *
   * @return The TunerInterface instance
   */
  public static synchronized TunerInterface getInstance() {
    if (s_instance == null) {
      s_instance = new TunerInterface();
    }
    return s_instance;
  }

  private TunerInterface() {
    m_ntInstance = NetworkTableInstance.getDefault();

    // Tuner status table
    NetworkTable tunerTable = m_ntInstance.getTable("Tuning").getSubTable("BayesianTuner");
    m_heartbeatSub = tunerTable.getDoubleTopic("Heartbeat").subscribe(0.0);
    m_tunerEnabledSub = tunerTable.getBooleanTopic("TunerEnabled").subscribe(true);
    m_tunerStatusSub = tunerTable.getStringTopic("TunerRuntimeStatus").subscribe("UNKNOWN");
    m_currentCoefficientSub = tunerTable.getStringTopic("CurrentCoefficient").subscribe("");
    m_shotCountSub = tunerTable.getDoubleTopic("ShotCount").subscribe(0.0);
    m_shotThresholdSub = tunerTable.getDoubleTopic("ShotThreshold").subscribe(10.0);

    // Interlock table
    NetworkTable interlockTable = m_ntInstance.getTable("FiringSolver").getSubTable("Interlock");
    m_requireShotLoggedSub = interlockTable.getBooleanTopic("RequireShotLogged").subscribe(false);
    m_requireCoeffUpdatedSub =
        interlockTable.getBooleanTopic("RequireCoefficientsUpdated").subscribe(false);
    m_shotLoggedSub = interlockTable.getBooleanTopic("ShotLogged").subscribe(true);
    m_coeffUpdatedSub = interlockTable.getBooleanTopic("CoefficientsUpdated").subscribe(true);

    // Fine-tuning table
    NetworkTable fineTuningTable = tunerTable.getSubTable("FineTuning");
    m_fineTuningEnabledSub = fineTuningTable.getBooleanTopic("FineTuningEnabled").subscribe(false);
    m_targetBiasSub = fineTuningTable.getStringTopic("TargetBias").subscribe("CENTER");
    m_biasAmountSub = fineTuningTable.getDoubleTopic("BiasAmount").subscribe(0.0);
  }

  /**
   * Checks if the Python tuner is connected and running.
   *
   * <p>The tuner updates a timestamp periodically. If it hasn't been updated recently, the tuner is
   * probably not running.
   *
   * @return true if tuner appears to be connected
   */
  public boolean isTunerConnected() {
    double heartbeat = m_heartbeatSub.get();
    double now = Timer.getFPGATimestamp();
    return (now - heartbeat) < 5.0;
  }

  /**
   * Checks if the tuner is enabled (not disabled by the driver).
   *
   * @return true if tuner is enabled on the dashboard
   */
  public boolean isTunerEnabled() {
    return m_tunerEnabledSub.get();
  }

  /**
   * Gets the current tuner status message.
   *
   * @return status string like "ACTIVE", "DISABLED", or "PAUSED"
   */
  public String getTunerStatus() {
    return m_tunerStatusSub.get();
  }

  /**
   * Gets the name of the coefficient currently being tuned.
   *
   * @return coefficient name, or empty string if not tuning
   */
  public String getCurrentCoefficient() {
    return m_currentCoefficientSub.get();
  }

  /**
   * Gets the current shot count toward the threshold.
   *
   * @return number of shots accumulated
   */
  public int getShotCount() {
    return (int) m_shotCountSub.get();
  }

  /**
   * Gets the shot threshold for auto-optimization.
   *
   * @return number of shots needed before optimization runs
   */
  public int getShotThreshold() {
    return (int) m_shotThresholdSub.get();
  }

  /**
   * Checks if shooting is allowed based on tuner interlocks.
   *
   * <p>If interlocks are enabled, shooting may be blocked until:
   *
   * <ul>
   *   <li>The previous shot has been logged by the tuner
   *   <li>Coefficients have been updated after optimization
   * </ul>
   *
   * @return true if shooting is allowed
   */
  public boolean isShootingAllowed() {
    boolean requireShotLogged = m_requireShotLoggedSub.get();
    boolean requireCoeffUpdated = m_requireCoeffUpdatedSub.get();

    // If no interlocks enabled, always allow
    if (!requireShotLogged && !requireCoeffUpdated) {
      return true;
    }

    // Check each interlock that's enabled
    if (requireShotLogged && !m_shotLoggedSub.get()) {
      return false;
    }

    if (requireCoeffUpdated && !m_coeffUpdatedSub.get()) {
      return false;
    }

    return true;
  }

  /**
   * Clears the shot logged flag before taking a shot.
   *
   * <p>Call this right before shooting if using the shot logging interlock. The tuner will set this
   * flag back to true once it has logged the shot.
   */
  public void clearShotLoggedFlag() {
    m_ntInstance
        .getTable("FiringSolver")
        .getSubTable("Interlock")
        .getEntry("ShotLogged")
        .setBoolean(false);
  }

  /**
   * Clears the coefficients updated flag.
   *
   * <p>Call this after reading new coefficients if using the coefficient update interlock.
   */
  public void clearCoefficientsUpdatedFlag() {
    m_ntInstance
        .getTable("FiringSolver")
        .getSubTable("Interlock")
        .getEntry("CoefficientsUpdated")
        .setBoolean(false);
  }

  /**
   * Checks if fine-tuning mode is enabled.
   *
   * @return true if fine-tuning is active
   */
  public boolean isFineTuningEnabled() {
    return m_fineTuningEnabledSub.get();
  }

  /**
   * Gets the target bias direction for fine-tuning.
   *
   * @return "CENTER", "LEFT", "RIGHT", "UP", or "DOWN"
   */
  public String getTargetBias() {
    return m_targetBiasSub.get();
  }

  /**
   * Gets the bias amount for fine-tuning (0.0 to 1.0).
   *
   * @return bias amount
   */
  public double getBiasAmount() {
    return m_biasAmountSub.get();
  }
}
