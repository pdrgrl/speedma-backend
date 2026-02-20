# Component: Marble Control Boards

## Overview
The system features three distinct marble control panels mounted on heavy bases, managing different aspects of the electrical topology:
1. **Main DC Control Board:** Manages the dynamo output and battery interaction.
2. **AC Grid Intake Board:** Manages the incoming three-phase power from the municipal grid.
3. **AC Motor Control Board:** Controls the ASEA induction motor.

## The Main DC Control Board & Battery Regulation
Because a dynamo's voltage varies with engine speed, and battery voltage varies with charge level, maintaining a steady 110V DC for the house required manual regulation.

- **Rheostat:** A high-power dissipation rheostat is wired in series with the dynamo to manually trim the output voltage.
- **Double-Selector Switch (The "End-Cell" Switch):** The 60-cell Tudor battery bank features electrical taps on the final 20 cells. The control board has a large coaxial double-selector switch.
  - This allows the operator to independently select how many cells are included in the *charging* circuit versus the *discharging* (house supply) circuit.
  - By adding or removing these final 20 cells from the circuit, the operator could adjust the output voltage to the house with a precision of about 2 Volts per click, compensating for the batteries dropping in voltage as they discharged.

## Instrumentation
The boards are fitted with high-quality early 20th-century Siemens & Halske analog panel meters, including a 160V voltmeter and a 30A ammeter, allowing the operator to monitor the system's live state during Scenarios B and C.
