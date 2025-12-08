// Copyright (c) FIRST and other WPILib contributors.
// Open Source Software; you can modify and/or share it under the terms of
// the WPILib BSD license file in the root directory of this project.

package frc.robot;

/**
 * Constants for the shooter/firing solver.
 *
 * <p><b>Instructions:</b> Add this {@code ShooterConstants} class inside your existing {@code
 * Constants.java} file.
 *
 * <pre>{@code
 * public final class Constants {
 *     // ... your existing constants ...
 *
 *     public static final class ShooterConstants {
 *         // ... copy the contents below ...
 *     }
 * }
 * }</pre>
 *
 * <p><b>IMPORTANT:</b> These constants are NEVER modified at runtime. The BayesOpt tuner modifies
 * operating values stored in the FiringSolver subsystem, not these defaults.
 */
public final class Constants {
  private Constants() {
    throw new UnsupportedOperationException("This is a utility class!");
  }

  /** Constants for the shooter subsystem and firing solver. */
  public static final class ShooterConstants {
    private ShooterConstants() {
      throw new UnsupportedOperationException("This is a utility class!");
    }

    // ========== TUNABLE COEFFICIENTS (defaults that can be tuned) ==========

    /**
     * Default drag coefficient for the projectile. Typical range: 0.3 - 0.6 for spherical objects.
     */
    public static final double kDefaultDragCoefficient = 0.47;

    /** Default air density in kg/m³. Sea level at 20°C is approximately 1.225 kg/m³. */
    public static final double kDefaultAirDensity = 1.225;

    /** Default projectile mass in kg. Adjust for your specific game piece. */
    public static final double kDefaultProjectileMass = 0.27; // ~270g

    /** Default cross-sectional area of projectile in m². For a sphere: π * r². */
    public static final double kDefaultProjectileArea = 0.0314; // ~10cm diameter

    /** Default number of iterations for velocity calculation. Higher = more accurate but slower. */
    public static final double kDefaultVelocityIterations = 10.0;

    /** Default gravity compensation factor. Adjust to fine-tune for gravity effects. */
    public static final double kDefaultGravityCompensation = 0.02;

    /** Default spin factor for Magnus effect. Adjust based on how spin affects your game piece. */
    public static final double kDefaultSpinFactor = 0.0;

    // ========== PHYSICAL LIMITS (NOT TUNED - used for validation) ==========

    /** Maximum shooting distance in meters. */
    public static final double kMaxDistanceMeters = 15.0;

    /** Minimum shooting distance in meters. */
    public static final double kMinDistanceMeters = 1.0;

    /** Maximum exit velocity in m/s. */
    public static final double kMaxVelocityMps = 25.0;

    /** Minimum exit velocity in m/s. */
    public static final double kMinVelocityMps = 5.0;

    /** Maximum pitch angle in radians. */
    public static final double kMaxPitchRadians = Math.toRadians(75);

    /** Minimum pitch angle in radians. */
    public static final double kMinPitchRadians = Math.toRadians(15);

    // ========== PHYSICAL PARAMETERS (NOT TUNED - measured constants) ==========

    /** Height of the launch point above the ground in meters. */
    public static final double kLaunchHeightMeters = 0.5;

    /** Standard target height in meters (e.g., hub height). */
    public static final double kTargetHeightMeters = 2.64;
  }
}
