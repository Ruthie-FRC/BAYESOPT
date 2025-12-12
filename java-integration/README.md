# Java Integration Files

These Java files integrate the BayesOpt tuner with your FRC robot code.
**All files follow standard WPILib conventions and use LoggedTunableNumber for tunable coefficients.**

## File Placement

Copy these files into your robot project at these locations:

```
your-robot-project/
└── src/main/java/frc/robot/
    ├── subsystems/
    │   └── FiringSolver.java           ← Copy here
    ├── util/
    │   ├── TunableNumber.java          ← Copy here (simple version)
    │   ├── LoggedTunableNumber.java    ← OR copy here (AdvantageKit version)
    │   └── TunerInterface.java         ← Copy here
    └── Constants.java                  ← Add the ShooterConstants class
```

## Quick Setup

### Step 1: Choose Your TunableNumber Implementation

**Option A: Simple (No AdvantageKit)**
- Copy `TunableNumber.java` to `src/main/java/frc/robot/util/`
- In `FiringSolver.java`, change the import to use `TunableNumber` instead of `LoggedTunableNumber`

**Option B: With AdvantageKit**
- Copy `LoggedTunableNumber.java` to `src/main/java/frc/robot/util/`
- Uses AdvantageKit's logging infrastructure
- Call `LoggedTunableNumber.logAll()` in your `Robot.periodic()`

**Option C: Use Your Existing LoggedTunableNumber**
- If you already have a LoggedTunableNumber class, just use that
- Update the import in `FiringSolver.java` to point to your version

### Step 2: Copy Files

1. Copy `FiringSolver.java` to `src/main/java/frc/robot/subsystems/`
2. Copy your chosen TunableNumber to `src/main/java/frc/robot/util/`
3. Copy `TunerInterface.java` to `src/main/java/frc/robot/util/`
4. Add the `ShooterConstants` class from `Constants_Addition.java` to your `Constants.java`

### Step 3: Use in Your Robot

In your `RobotContainer.java`:

```java
import frc.robot.subsystems.FiringSolver;

public class RobotContainer {
  // Create the subsystem
  private final FiringSolver m_firingSolver = new FiringSolver();

  public RobotContainer() {
    // Configure default commands, button bindings, etc.
  }

  // In your shoot command, call:
  // m_firingSolver.logShot(hit, distance, pitch, velocity, yaw);
}
```

### Step 4: Run the Python Tuner

On your Driver Station laptop:
1. Double-click `START_TUNER.bat`
2. The tuner connects via NetworkTables
3. Fire shots - the tuner will optimize the LoggedTunableNumber values automatically

## How LoggedTunableNumber Works

```java
// Define a tunable coefficient
private static final LoggedTunableNumber m_dragCoefficient =
    new LoggedTunableNumber("FiringSolver/kDragCoefficient", 0.47);

// Use it in your calculations
double drag = m_dragCoefficient.get();

// The Python tuner writes to:
// NetworkTables: /Tuning/Coefficients/kDragCoefficient

// The LoggedTunableNumber automatically picks up the new value!
```

## WPILib Conventions Used

- **Naming**: `m_` prefix for member variables, `k` prefix for constants, `s_` for static
- **LoggedTunableNumber**: All tunable coefficients use LoggedTunableNumber pattern
- **Sendable**: FiringSolver implements `initSendable()` for dashboard integration
- **NetworkTables 4**: Uses modern pub/sub API with proper topics
- **Package structure**: Standard `frc.robot.subsystems` and `frc.robot.util`
- **Copyright header**: WPILib BSD license header
- **Javadoc**: Full documentation on all public methods
- **Singleton pattern**: TunerInterface uses `getInstance()` pattern

## Files Included

| File | Purpose |
|------|---------|
| `FiringSolver.java` | Main subsystem with LoggedTunableNumber coefficients |
| `TunableNumber.java` | Simple tunable number (no AdvantageKit) |
| `LoggedTunableNumber.java` | Full logging version (with AdvantageKit) |
| `TunerInterface.java` | Helper for checking tuner status and interlocks |
| `Constants_Addition.java` | ShooterConstants class to add to your Constants.java |

## How It Works

```
Driver Station Laptop              Robot (RoboRIO)
┌─────────────────────┐            ┌─────────────────────┐
│  Python Tuner       │◄──────────►│  Java Code          │
│  (START_TUNER.bat)  │ NetworkTables│  (FiringSolver.java)│
│                     │            │                     │
│  • Reads shots      │            │  • Publishes shots  │
│  • Runs optimization│            │  • LoggedTunableNumber│
│  • Writes to /Tuning│            │    reads new values │
└─────────────────────┘            └─────────────────────┘
```

## Important Notes

- **LoggedTunableNumber** - All coefficients are LoggedTunableNumbers that can be tuned at runtime
- **Constants.java is NEVER modified** - Only the LoggedTunableNumber values change
- The tuner runs on your laptop, not on the RoboRIO
- All communication happens through NetworkTables at `/Tuning/Coefficients/`
- Coefficient updates are immediate - LoggedTunableNumber picks them up automatically
- Uses NetworkTables 4 pub/sub API for better performance

## See Also

- **Java Integration Guide:** [../bayesopt/docs/JAVA_INTEGRATION.md](../bayesopt/docs/JAVA_INTEGRATION.md) - Detailed integration instructions
- **User Guide:** [../bayesopt/docs/USER_GUIDE.md](../bayesopt/docs/USER_GUIDE.md) - Complete tuner documentation
- **Setup Guide:** [../bayesopt/docs/SETUP.md](../bayesopt/docs/SETUP.md) - Installation instructions
- **Main README:** [../README.md](../README.md) - Project overview
- **Documentation Index:** //TODO: add link later
  
