# Java Robot Code Integration Guide

This guide explains how to integrate the BayesOpt Python tuner with your Java robot code.

## Ready-to-Use Java Files

**Copy these files from the `java-integration/` folder into your robot project:**

| File | Copy To | Purpose |
|------|---------|---------|
| `FiringSolver.java` | `src/main/java/frc/robot/subsystems/` | Main subsystem with tuner integration |
| `TunerInterface.java` | `src/main/java/frc/robot/util/` | Helper for tuner communication |
| `Constants_Addition.java` | (merge into your `Constants.java`) | Default coefficient values |

See `java-integration/README.md` for detailed setup instructions.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DRIVER STATION LAPTOP                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  BayesOpt Python App (double-click START_TUNER.bat)               │  │
│  │  • Runs Bayesian optimization calculations                        │  │
│  │  • Displays GUI with status, logs, controls                       │  │
│  │  • Publishes coefficient updates to NetworkTables                 │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                   │                                     │
│                                   │ NetworkTables (via WiFi/Ethernet)   │
│                                   ▼                                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │
┌─────────────────────────────────────────────────────────────────────────┐
│                              ROBOT                                      │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  Java Robot Code (on RoboRIO)                                     │  │
│  │  • Reads coefficient values from NetworkTables                    │  │
│  │  • Publishes shot data (hit/miss, distance, velocity, etc.)      │  │
│  │  • Uses coefficients in FiringSolver calculations                 │  │
│  │  • NEVER MODIFIES Constants.java or protected values              │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                   │                                     │
│                                   ▼                                     │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  RoboRIO                                                          │  │
│  │  • Executes motor commands                                        │  │
│  │  • Runs all real-time control                                     │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## What the Python Tuner Does

1. **Runs on the Driver Station laptop** (NOT on the RoboRIO)
2. **Connects via NetworkTables** to the robot over WiFi/Ethernet
3. **Reads shot data** from `/FiringSolver/` table
4. **Runs Bayesian optimization** calculations on the laptop
5. **Writes updated coefficients** to `/Tuning/` table
6. **Publishes dashboard controls** to `/Tuning/BayesianTuner/`

## What Your Java Code Needs to Do

### 1. Publish Shot Data (After Every Shot)

When the robot fires a shot, publish the result to NetworkTables:

```java
// In your FiringSolver or Shooter subsystem
import edu.wpi.first.networktables.NetworkTable;
import edu.wpi.first.networktables.NetworkTableInstance;

public class FiringSolver {
    private final NetworkTable shotTable;
    
    public FiringSolver() {
        shotTable = NetworkTableInstance.getDefault().getTable("/FiringSolver");
    }
    
    /**
     * Call this after every shot to log the result for the tuner.
     * 
     * @param hit True if the shot hit the target
     * @param distance Distance to target in meters
     * @param pitchRadians Launch angle in radians
     * @param exitVelocity Exit velocity in m/s
     * @param yawRadians Yaw angle in radians
     */
    public void logShotResult(boolean hit, double distance, 
                              double pitchRadians, double exitVelocity,
                              double yawRadians) {
        // Timestamp (used to detect new shots)
        shotTable.getEntry("ShotTimestamp").setDouble(Timer.getFPGATimestamp());
        
        // Shot result
        shotTable.getEntry("Hit").setBoolean(hit);
        shotTable.getEntry("Distance").setDouble(distance);
        
        // Solution values
        NetworkTable solutionTable = shotTable.getSubTable("Solution");
        solutionTable.getEntry("pitchRadians").setDouble(pitchRadians);
        solutionTable.getEntry("exitVelocity").setDouble(exitVelocity);
        solutionTable.getEntry("yawRadians").setDouble(yawRadians);
        
        // Physical parameters at time of shot (for logging)
        shotTable.getEntry("TargetHeight").setDouble(targetHeightMeters);
        shotTable.getEntry("LaunchHeight").setDouble(launchHeightMeters);
        
        // Current coefficient values at time of shot
        shotTable.getEntry("DragCoefficient").setDouble(currentDragCoeff);
        shotTable.getEntry("AirDensity").setDouble(currentAirDensity);
        shotTable.getEntry("ProjectileMass").setDouble(currentMass);
        shotTable.getEntry("ProjectileArea").setDouble(currentArea);
    }
}
```

### 2. Read Updated Coefficients

Read the tuned coefficients from NetworkTables and use them in calculations:

```java
public class FiringSolver {
    private final NetworkTable tuningTable;
    
    // Operating values (updated from NetworkTables)
    private double dragCoefficient;
    private double airDensity;
    private double projectileMass;
    // ... etc
    
    public FiringSolver() {
        tuningTable = NetworkTableInstance.getDefault().getTable("/Tuning");
        
        // Initialize with defaults from code
        dragCoefficient = Constants.Shooter.DEFAULT_DRAG_COEFFICIENT;
        airDensity = Constants.Shooter.DEFAULT_AIR_DENSITY;
        projectileMass = Constants.Shooter.DEFAULT_PROJECTILE_MASS;
    }
    
    /**
     * Call this in periodic() to read updated coefficients from the tuner.
     * This does NOT modify Constants.java - only the operating values.
     */
    public void updateCoefficientsFromTuner() {
        // Read from /Tuning/Coefficients/ table
        // The Python tuner writes updated values here
        
        dragCoefficient = tuningTable.getSubTable("Coefficients")
            .getEntry("kDragCoefficient")
            .getDouble(Constants.Shooter.DEFAULT_DRAG_COEFFICIENT);
        
        airDensity = tuningTable.getSubTable("Coefficients")
            .getEntry("kAirDensity")
            .getDouble(Constants.Shooter.DEFAULT_AIR_DENSITY);
        
        projectileMass = tuningTable.getSubTable("Coefficients")
            .getEntry("kProjectileMass")
            .getDouble(Constants.Shooter.DEFAULT_PROJECTILE_MASS);
        
        // Use these operating values in your calculations
        // The Constants.java file is NEVER modified
    }
    
    /**
     * Calculate firing solution using the current (possibly tuned) coefficients.
     */
    public FiringSolution calculate(double distance, double targetHeight) {
        // Use the operating values (dragCoefficient, airDensity, etc.)
        // NOT the Constants.java values directly
        
        double drag = 0.5 * airDensity * dragCoefficient * projectileArea;
        // ... rest of calculation
    }
}
```

### 3. Key NetworkTables Paths

| Path | Direction | Purpose |
|------|-----------|---------|
| `/FiringSolver/ShotTimestamp` | Robot → Tuner | Timestamp of last shot (used to detect new shots) |
| `/FiringSolver/Hit` | Robot → Tuner | Whether the shot hit (true/false) |
| `/FiringSolver/Distance` | Robot → Tuner | Distance to target in meters |
| `/FiringSolver/Solution/pitchRadians` | Robot → Tuner | Launch angle used |
| `/FiringSolver/Solution/exitVelocity` | Robot → Tuner | Exit velocity used |
| `/Tuning/Coefficients/*` | Tuner → Robot | Updated coefficient values |
| `/Tuning/BayesianTuner/*` | Tuner → Dashboard | Dashboard controls and status |

## Important Rules

### DO NOT Modify:
- ❌ Constants.java
- ❌ Any final static values
- ❌ Hardware-related constants
- ❌ Safety limits

### DO:
- ✅ Read operating coefficients from NetworkTables
- ✅ Store operating values in non-final member variables
- ✅ Use the operating values in calculations
- ✅ Fall back to Constants.java defaults if NetworkTables values are missing

## Example: Complete FiringSolver Integration

```java
package frc.robot.subsystems;

import edu.wpi.first.networktables.*;
import edu.wpi.first.wpilibj.Timer;
import edu.wpi.first.wpilibj2.command.SubsystemBase;
import frc.robot.Constants;

public class FiringSolver extends SubsystemBase {
    
    private final NetworkTableInstance ntInstance;
    private final NetworkTable shotTable;
    private final NetworkTable tuningTable;
    private final NetworkTable coeffTable;
    
    // Operating coefficients (read from tuner, NOT from Constants)
    private double dragCoefficient;
    private double airDensity;
    private double projectileMass;
    private double projectileArea;
    private double velocityIterationCount;
    
    public FiringSolver() {
        ntInstance = NetworkTableInstance.getDefault();
        shotTable = ntInstance.getTable("/FiringSolver");
        tuningTable = ntInstance.getTable("/Tuning");
        coeffTable = tuningTable.getSubTable("Coefficients");
        
        // Initialize with code defaults
        resetToDefaults();
    }
    
    /**
     * Reset operating values to code defaults.
     */
    public void resetToDefaults() {
        dragCoefficient = Constants.Shooter.DEFAULT_DRAG_COEFFICIENT;
        airDensity = Constants.Shooter.DEFAULT_AIR_DENSITY;
        projectileMass = Constants.Shooter.DEFAULT_PROJECTILE_MASS;
        projectileArea = Constants.Shooter.DEFAULT_PROJECTILE_AREA;
        velocityIterationCount = Constants.Shooter.DEFAULT_VELOCITY_ITERATIONS;
    }
    
    @Override
    public void periodic() {
        // Read updated coefficients from tuner (if connected)
        updateCoefficientsFromTuner();
    }
    
    private void updateCoefficientsFromTuner() {
        // Only update if the tuner has written values
        // Falls back to current operating values (not Constants) if not present
        
        dragCoefficient = coeffTable.getEntry("kDragCoefficient")
            .getDouble(dragCoefficient);
        
        airDensity = coeffTable.getEntry("kAirDensity")
            .getDouble(airDensity);
        
        projectileMass = coeffTable.getEntry("kProjectileMass")
            .getDouble(projectileMass);
        
        projectileArea = coeffTable.getEntry("kProjectileArea")
            .getDouble(projectileArea);
        
        velocityIterationCount = coeffTable.getEntry("kVelocityIterationCount")
            .getDouble(velocityIterationCount);
    }
    
    /**
     * Log a shot result for the tuner to analyze.
     */
    public void logShot(boolean hit, double distance, double pitch, 
                        double velocity, double yaw) {
        shotTable.getEntry("ShotTimestamp").setDouble(Timer.getFPGATimestamp());
        shotTable.getEntry("Hit").setBoolean(hit);
        shotTable.getEntry("Distance").setDouble(distance);
        
        NetworkTable solution = shotTable.getSubTable("Solution");
        solution.getEntry("pitchRadians").setDouble(pitch);
        solution.getEntry("exitVelocity").setDouble(velocity);
        solution.getEntry("yawRadians").setDouble(yaw);
        
        // Log current coefficients at time of shot
        shotTable.getEntry("DragCoefficient").setDouble(dragCoefficient);
        shotTable.getEntry("AirDensity").setDouble(airDensity);
        shotTable.getEntry("ProjectileMass").setDouble(projectileMass);
        shotTable.getEntry("ProjectileArea").setDouble(projectileArea);
    }
    
    /**
     * Calculate firing solution using tuned coefficients.
     */
    public FiringSolution calculate(double distanceMeters, double targetHeightMeters) {
        // Use the operating values, which may have been updated by the tuner
        double dragForce = 0.5 * airDensity * dragCoefficient * projectileArea;
        
        // ... your calculation logic here ...
        
        return new FiringSolution(pitch, velocity, yaw);
    }
    
    // Getters for current operating values (for logging/display)
    public double getDragCoefficient() { return dragCoefficient; }
    public double getAirDensity() { return airDensity; }
    public double getProjectileMass() { return projectileMass; }
}
```

## Testing the Integration

1. **Deploy robot code** with the NetworkTables integration
2. **Connect laptop** to robot network
3. **Double-click START_TUNER.bat** on the laptop
4. **Check connection** - the GUI should show "Connected" status
5. **Fire a shot** - the tuner should log it
6. **Check dashboard** - controls should appear at `/Tuning/BayesianTuner/`

## Troubleshooting

### "Not receiving shot data"
- Verify `logShot()` is being called after each shot
- Check that `ShotTimestamp` is updating in NetworkTables
- Verify robot and laptop are on the same network

### "Coefficients not updating"
- Verify `updateCoefficientsFromTuner()` is being called in `periodic()`
- Check that you're using the operating values (not Constants) in calculations
- Verify the tuner is connected and running optimization

### "Dashboard controls missing"
- The controls appear at `/Tuning/BayesianTuner/`
- They only appear when the Python tuner is running
- Check Shuffleboard/AdvantageKit for the correct path

## See Also

- **Java Integration Files:** [java-integration/README.md](../../java-integration/README.md) - Java file documentation
- **User Guide:** [USER_GUIDE.md](USER_GUIDE.md) - Complete tuner documentation
- **Setup Guide:** [SETUP.md](SETUP.md) - Installation instructions
- **Troubleshooting:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common problems and solutions
- **Developer Guide:** [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - Architecture and code structure
