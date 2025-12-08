package frc.robot.subsystems;

import edu.wpi.first.networktables.BooleanPublisher;
import edu.wpi.first.networktables.DoublePublisher;
import edu.wpi.first.networktables.NetworkTable;
import edu.wpi.first.networktables.NetworkTableInstance;
import edu.wpi.first.util.sendable.SendableBuilder;
import edu.wpi.first.wpilibj.Timer;
import edu.wpi.first.wpilibj2.command.SubsystemBase;
import frc.robot.Constants.ShooterConstants;
import frc.robot.util.LoggedTunableNumber;
import org.littletonrobotics.junction.Logger; // AK logging

/**
 * FiringSolver subsystem integrating Bayesian optimization tuning with robust physics calculation.
 * Combines NetworkTables/tuner interoperability with iterative ballistics solver.
 */
public class FiringSolver extends SubsystemBase {
  // === Tunable coefficients (LoggedTunableNumber + NetworkTables publish) ===
  private static final LoggedTunableNumber m_dragCoefficient =
      new LoggedTunableNumber("DragCoefficient", ShooterConstants.kDefaultDragCoefficient);

  private static final LoggedTunableNumber m_airDensity =
      new LoggedTunableNumber("AirDensity", ShooterConstants.kDefaultAirDensity);

  private static final LoggedTunableNumber m_projectileMass =
      new LoggedTunableNumber("ProjectileMass", ShooterConstants.kDefaultProjectileMass);

  private static final LoggedTunableNumber m_projectileArea =
      new LoggedTunableNumber("ProjectileArea", ShooterConstants.kDefaultProjectileArea);

  private static final LoggedTunableNumber m_velocityIterations =
      new LoggedTunableNumber("VelocityIterations", ShooterConstants.kDefaultVelocityIterations);

  private static final LoggedTunableNumber m_angleIterations =
      new LoggedTunableNumber("AngleIterations", 20);

  private static final LoggedTunableNumber m_velocityTolerance =
      new LoggedTunableNumber("VelocityTolerance", 0.01);

  private static final LoggedTunableNumber m_angleTolerance =
      new LoggedTunableNumber("AngleTolerance", 1e-4);

  private static final LoggedTunableNumber m_gravityCompensation =
      new LoggedTunableNumber("GravityCompensation", ShooterConstants.kDefaultGravityCompensation);

  private static final LoggedTunableNumber m_spinFactor =
      new LoggedTunableNumber("SpinFactor", ShooterConstants.kDefaultSpinFactor);

  private static final LoggedTunableNumber m_maxExitVelocity =
      new LoggedTunableNumber("MaxExitVelocity", ShooterConstants.kDefaultMaxExitVelocity);

  // === Shot data publishers (NetworkTables) ===
  private final DoublePublisher m_shotTimestampPub;
  private final BooleanPublisher m_hitPub;
  private final DoublePublisher m_distancePub;
  private final DoublePublisher m_pitchPub;
  private final DoublePublisher m_velocityPub;
  private final DoublePublisher m_yawPub;
  private final DoublePublisher m_targetHeightPub;
  private final DoublePublisher m_launchHeightPub;
  private final DoublePublisher m_dragCoeffPub;
  private final DoublePublisher m_airDensityPub;
  private final DoublePublisher m_projectileMassPub;
  private final DoublePublisher m_projectileAreaPub;

  // === Physics constants ===
  private static final double GRAVITY = 9.80665;

  /** Creates a new FiringSolver subsystem. */
  public FiringSolver() {
    NetworkTableInstance inst = NetworkTableInstance.getDefault();

    NetworkTable shotTable = inst.getTable("FiringSolver");
    NetworkTable solutionTable = shotTable.getSubTable("Solution");

    m_shotTimestampPub = shotTable.getDoubleTopic("ShotTimestamp").publish();
    m_hitPub = shotTable.getBooleanTopic("Hit").publish();
    m_distancePub = shotTable.getDoubleTopic("Distance").publish();
    m_targetHeightPub = shotTable.getDoubleTopic("TargetHeight").publish();
    m_launchHeightPub = shotTable.getDoubleTopic("LaunchHeight").publish();
    m_dragCoeffPub = shotTable.getDoubleTopic("DragCoefficient").publish();
    m_airDensityPub = shotTable.getDoubleTopic("AirDensity").publish();
    m_projectileMassPub = shotTable.getDoubleTopic("ProjectileMass").publish();
    m_projectileAreaPub = shotTable.getDoubleTopic("ProjectileArea").publish();

    m_pitchPub = solutionTable.getDoubleTopic("pitchRadians").publish();
    m_velocityPub = solutionTable.getDoubleTopic("exitVelocity").publish();
    m_yawPub = solutionTable.getDoubleTopic("yawRadians").publish();
  }

  // === Shot logging ===

  /**
   * Logs a shot result and solution for BayesOpt tuner analysis,
   * including hit/miss, measured parameters and the solver outputs.
   */
  public void logShot(
      boolean hit,
      double distanceMeters,
      double pitchRadians,
      double exitVelocityMps,
      double yawRadians) {

    m_shotTimestampPub.set(Timer.getFPGATimestamp());
    m_hitPub.set(hit);
    m_distancePub.set(distanceMeters);

    m_pitchPub.set(pitchRadians);
    m_velocityPub.set(exitVelocityMps);
    m_yawPub.set(yawRadians);

    m_dragCoeffPub.set(m_dragCoefficient.get());
    m_airDensityPub.set(m_airDensity.get());
    m_projectileMassPub.set(m_projectileMass.get());
    m_projectileAreaPub.set(m_projectileArea.get());

    // AdvantageKit/NT logging
    Logger.recordOutput("FiringSolver/Hit", hit);
    Logger.recordOutput("FiringSolver/Solution",
        new FiringSolution(pitchRadians, exitVelocityMps, yawRadians));
  }

  /** Overloaded logShot for more parameters (target/launch heights). */
  public void logShot(
      boolean hit,
      double distanceMeters,
      double pitchRadians,
      double exitVelocityMps,
      double yawRadians,
      double targetHeightMeters,
      double launchHeightMeters) {
    logShot(hit, distanceMeters, pitchRadians, exitVelocityMps, yawRadians);
    m_targetHeightPub.set(targetHeightMeters);
    m_launchHeightPub.set(launchHeightMeters);

    Logger.recordOutput("FiringSolver/TargetHeight", targetHeightMeters);
    Logger.recordOutput("FiringSolver/LaunchHeight", launchHeightMeters);
  }

  // === Robust physics firing solution solver ===

  /**
   * Calculates a firing solution using robust physics model and fully tunable parameters.
   *
   * @param distanceMeters Distance to target in meters (horizontal)
   * @param targetHeightMeters Height of target in meters
   * @param launchHeightMeters Height of launch point in meters
   * @return FiringSolution (pitch, velocity, yaw)
   */
  public FiringSolution calculate(
      double distanceMeters, double targetHeightMeters, double launchHeightMeters) {
    // Get current coefficient values
    double dragCoeff = m_dragCoefficient.get();
    double airDensity = m_airDensity.get();
    double projectileArea = m_projectileArea.get();
    double projectileMass = m_projectileMass.get();
    double gravityComp = m_gravityCompensation.get();
    double velocityIterations = m_velocityIterations.get();
    double angleIterations = m_angleIterations.get();
    double velocityTolerance = m_velocityTolerance.get();
    double angleTolerance = m_angleTolerance.get();
    double maxExitVelocity = m_maxExitVelocity.get();

    double heightDiff = targetHeightMeters - launchHeightMeters;
    double yaw = 0.0; // Simplified, for 2D shot; extend for full 3D as needed.

    // === Iterative velocity calculation (adapts SideKick logic) ===
    double v0 = 10.0;
    int vIters = (int) Math.max(1, velocityIterations);
    for (int i = 0; i < vIters; i++) {
      double dragAccel =
          0.5 * airDensity * dragCoeff * projectileArea * v0 * v0 / projectileMass;
      double t = distanceMeters / Math.max(1e-5, v0);
      double estDrop = 0.5 * GRAVITY * t * t + 0.5 * dragAccel * t * t;
      double error = estDrop - heightDiff;
      v0 -= error * 0.5;
      v0 = Math.max(2.0, Math.min(maxExitVelocity, v0));
      if (Math.abs(error) < velocityTolerance) break;
    }

    // === Iterative angle calculation ===
    double pitch = 0.4; // initial guess radians
    int aIters = (int) Math.max(1, angleIterations);
    for (int i = 0; i < aIters; i++) {
      double sin = Math.sin(pitch);
      double cos = Math.cos(pitch);
      double t = distanceMeters / Math.max(1e-5, (v0 * cos));
      double y = v0 * sin * t - 0.5 * GRAVITY * t * t - heightDiff;
      double dyda = v0 * cos * t + 1e-6; // prevent zero division
      pitch -= y / dyda;
      if (Math.abs(y) < angleTolerance) break;
    }
    pitch += gravityComp; // add gravity compensation offset

    // === Record solution ===
    Logger.recordOutput("FiringSolver/SolutionIterative",
        new FiringSolution(pitch, v0, yaw));

    return new FiringSolution(pitch, v0, yaw);
  }

  @Override
  public void periodic() {
    // LoggedTunableNumbers automatically update (NT/AK integration)
  }

  @Override
  public void initSendable(SendableBuilder builder) {
    super.initSendable(builder);
    builder.addDoubleProperty("DragCoefficient", m_dragCoefficient::get, null);
    builder.addDoubleProperty("AirDensity", m_airDensity::get, null);
    builder.addDoubleProperty("ProjectileMass", m_projectileMass::get, null);
    builder.addDoubleProperty("ProjectileArea", m_projectileArea::get, null);
    builder.addDoubleProperty("VelocityIterations", m_velocityIterations::get, null);
    builder.addDoubleProperty("AngleIterations", m_angleIterations::get, null);
    builder.addDoubleProperty("VelocityTolerance", m_velocityTolerance::get, null);
    builder.addDoubleProperty("AngleTolerance", m_angleTolerance::get, null);
    builder.addDoubleProperty("MaxExitVelocity", m_maxExitVelocity::get, null);
    builder.addDoubleProperty("GravityCompensation", m_gravityCompensation::get, null);
    builder.addDoubleProperty("SpinFactor", m_spinFactor::get, null);
  }

  // === Tunable getters ===

  public double getDragCoefficient() {
    return m_dragCoefficient.get();
  }
  public double getAirDensity() {
    return m_airDensity.get();
  }
  public double getProjectileMass() {
    return m_projectileMass.get();
  }
  public double getProjectileArea() {
    return m_projectileArea.get();
  }
  public double getVelocityIterationCount() { return m_velocityIterations.get(); }
  public double getAngleIterationCount() { return m_angleIterations.get(); }
  public double getVelocityTolerance() { return m_velocityTolerance.get(); }
  public double getAngleTolerance() { return m_angleTolerance.get(); }
  public double getGravityCompensation() { return m_gravityCompensation.get(); }
  public double getSpinFactor() { return m_spinFactor.get(); }
  public double getMaxExitVelocity() { return m_maxExitVelocity.get(); }

  /** Container for a firing solution result. */
  public static class FiringSolution {
    private final double m_pitchRadians;
    private final double m_exitVelocityMps;
    private final double m_yawRadians;

    public FiringSolution(double pitchRadians, double exitVelocityMps, double yawRadians) {
      m_pitchRadians = pitchRadians;
      m_exitVelocityMps = exitVelocityMps;
      m_yawRadians = yawRadians;
    }

    public double getPitchRadians() {
      return m_pitchRadians;
    }
    public double getExitVelocityMps() {
      return m_exitVelocityMps;
    }
    public double getYawRadians() {
      return m_yawRadians;
    }

    @Override
    public String toString() {
      return String.format(
          "FiringSolution[pitch=%.3f rad, vel=%.2f m/s, yaw=%.3f rad]",
          m_pitchRadians, m_exitVelocityMps, m_yawRadians);
    }
  }
}
