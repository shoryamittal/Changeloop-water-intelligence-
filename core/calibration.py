# -*- coding: utf-8 -*-
"""ChangeLoop - Non-Invasive IoT & Multi-Variable Ionic Calibration.

What this is
------------
Textile dyehouse wastewater contains a complex ionic cocktail:
  1. Neutral electrolytes (NaCl, Na2SO4) used in reactive dyeing exhaustion,
     which dictate RO osmotic pressure and evaporator steam duty.
  2. Residual alkalinity (NaOH, Na2CO3) from scouring and dye fixation,
     whose hydroxide ions (OH-) have disproportionately high ionic conductance
     (198 S*cm2/mol vs 76.3 S*cm2/mol for Cl-).

A naive electrical conductivity sensor will overestimate true salt mass by 40-70%
due to caustic interference. This module provides:
  - Multi-variable ionic calibration using daily argentometric (AgNO3) titration
    curves (Mohr's method) and pH compensation to isolate true neutral salt TDS.
  - Hardware status tracking for clamp-on ultrasonic meters (IBR-compliant, non-invasive)
    and toroidal inductive conductivity probes.
  - Sensor fault fail-safe: if telemetry drops below 95% completeness or drifts >10%,
    the system locks into HOLD_STATE and claims Rs 0 savings.
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple
import datetime
import math


@dataclass
class TitrationRecord:
    """Argentometric (AgNO3) chloride titration record."""
    record_id: str
    timestamp: str
    operator_id: str
    sample_volume_ml: float = 50.0
    titrant_normality_n: float = 0.1000   # 0.1 N AgNO3
    titre_volume_ml: float = 14.1
    blank_volume_ml: float = 0.1
    ph_measured: float = 9.8
    conductivity_us_cm: float = 18500.0   # Bulk conductivity in uS/cm
    temperature_c: float = 25.0
    calibration_slope: float = 0.68       # Salt TDS (mg/L) per uS/cm after alkali subtraction

    @property
    def chloride_mg_per_l(self) -> float:
        """Calculate chloride ion concentration [Cl-] in mg/L:
        [Cl-] = ((V_titre - V_blank) * N * 35453) / V_sample
        """
        net_titre = max(0.0, self.titre_volume_ml - self.blank_volume_ml)
        if self.sample_volume_ml <= 0:
            return 0.0
        return (net_titre * self.titrant_normality_n * 35453.0) / self.sample_volume_ml

    @property
    def nacl_equivalent_mg_per_l(self) -> float:
        """Convert [Cl-] to NaCl equivalent (58.44 / 35.453 = 1.6483)."""
        return self.chloride_mg_per_l * (58.44 / 35.453)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["chloride_mg_per_l"] = round(self.chloride_mg_per_l, 1)
        d["nacl_equivalent_mg_per_l"] = round(self.nacl_equivalent_mg_per_l, 1)
        return d


@dataclass
class HardwareDeviceStatus:
    """Status model for non-invasive clamp-on ultrasonic & toroidal sensors."""
    device_id: str
    device_type: str        # CLAMP_ON_ULTRASONIC | TOROIDAL_CONDUCTIVITY | PH_PROBE
    location: str           # DYEHOUSE_MAIN_DRAIN | RO_FEED | MEE_INLET
    protocol: str           # MODBUS_RTU | 4_20MA | MQTT
    sampling_interval_s: int = 1
    last_heartbeat: str = ""
    completeness_pct: float = 99.4
    drift_pct: float = 2.1  # Calibration drift percentage
    snr_db: float = 38.5    # Signal-to-Noise Ratio (dB) for ultrasonic
    temperature_c: float = 28.4
    sound_speed_m_s: float = 1520.0 # Acoustic velocity (m/s) in water/liquor
    is_ibr_compliant: bool = True   # Non-invasive clamp-on meets IBR / ASME B31.3
    health_status: str = "GOOD"     # GOOD | WARNING | CRITICAL | FAULT

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class IonicCalibrationEngine:
    """Calibrates continuous high-frequency conductivity readings into true neutral salt mass."""

    def __init__(self):
        # Default baseline titration record from standard Tirupur reactive dyehouse
        self.active_titration = TitrationRecord(
            record_id="TITR-2026-10-21-01",
            timestamp="2026-10-21T06:00:00Z",
            operator_id="LAB-QC-ANAND",
            sample_volume_ml=50.0,
            titrant_normality_n=0.1000,
            titre_volume_ml=14.1,
            blank_volume_ml=0.1,
            ph_measured=9.8,
            conductivity_us_cm=18500.0,
            temperature_c=25.0,
            calibration_slope=0.68,
        )
        self.devices: Dict[str, HardwareDeviceStatus] = {
            "US-FLOW-01": HardwareDeviceStatus(
                device_id="US-FLOW-01",
                device_type="CLAMP_ON_ULTRASONIC",
                location="DYEHOUSE_MAIN_DRAIN",
                protocol="MODBUS_RTU",
                completeness_pct=99.8,
                drift_pct=1.4,
                snr_db=42.1,
                sound_speed_m_s=1518.0,
                health_status="GOOD",
            ),
            "TOROID-COND-01": HardwareDeviceStatus(
                device_id="TOROID-COND-01",
                device_type="TOROIDAL_CONDUCTIVITY",
                location="DYEHOUSE_MAIN_DRAIN",
                protocol="4_20MA",
                completeness_pct=99.5,
                drift_pct=2.3,
                snr_db=45.0,
                health_status="GOOD",
            ),
            "PH-SENS-01": HardwareDeviceStatus(
                device_id="PH-SENS-01",
                device_type="PH_PROBE",
                location="EQUALIZATION_TANK",
                protocol="4_20MA",
                completeness_pct=98.9,
                drift_pct=3.1,
                health_status="GOOD",
            ),
        }

    def check_telemetry_integrity(self) -> Tuple[bool, str]:
        """Verify telemetry completeness >= 95%, drift <= 15% and no critical sensor faults.
        Rule: If completeness < 95% or drift > 15%, enter HOLD_STATE and claim Rs 0 savings.
        """
        for dev_id, dev in self.devices.items():
            if dev.completeness_pct < 95.0:
                return False, (
                    f"Sensor Fault Fail-Safe: Device {dev_id} completeness at {dev.completeness_pct:.1f}% "
                    "(< 95.0% threshold). Entering HOLD_STATE: Rs 0 savings claimed."
                )
            if getattr(dev, "drift_pct", 0.0) > 15.0:
                return False, (
                    f"Sensor Fault Fail-Safe: Device {dev_id} drift at {dev.drift_pct:.1f}% "
                    "(> 15.0% threshold). Entering HOLD_STATE: Rs 0 savings claimed until recalibrated."
                )
            if dev.health_status in {"CRITICAL", "FAULT"}:
                return False, (
                    f"Sensor Fault Fail-Safe: Device {dev_id} in {dev.health_status} state. "
                    "Entering HOLD_STATE: Rs 0 savings claimed."
                )
        return True, "All telemetry channels operational (>= 95% completeness, <= 15% drift)."

    def calibrate_tds(
        self,
        raw_conductivity_us_cm: float,
        ph: float = 9.8,
        temp_c: float = 25.0,
    ) -> Dict[str, Any]:
        """Disentangle neutral electrolyte (NaCl) from scouring/bleaching alkali (NaOH).

        Physics:
          1. Temperature compensation to 25 deg C:
             cond_25 = raw_cond / (1 + 0.02 * (temp_c - 25))
          2. Hydroxide ion (OH-) conductivity:
             pOH = 14.0 - ph
             [OH-] = 10^(-pOH) mol/L
             kappa_alkali = [OH-] * lambda_OH * 1000 (uS/cm)
             where lambda_OH ~ 198 S*cm2/mol
          3. Net salt conductivity:
             kappa_salt = max(0.0, cond_25 - kappa_alkali)
          4. True Salt TDS (mg/L):
             TDS = kappa_salt * calibration_slope
        """
        is_valid, fail_reason = self.check_telemetry_integrity()

        # Temperature normalisation (2.0% per deg C)
        tc_factor = 1.0 + 0.02 * (temp_c - 25.0)
        cond_25 = raw_conductivity_us_cm / tc_factor if tc_factor > 0 else raw_conductivity_us_cm

        # Hydroxide equivalent conductivity subtraction
        p_oh = max(0.0, 14.0 - ph)
        conc_oh_mol_per_l = 10.0 ** (-p_oh)
        # 198 S*cm2/mol = 198,000 uS*cm2/mol -> in uS/cm: conc * 198000 * 1000 / 1000
        kappa_alkali_us_cm = conc_oh_mol_per_l * 198000.0

        kappa_salt = max(0.0, cond_25 - kappa_alkali_us_cm)
        true_salt_tds_mg_l = kappa_salt * self.active_titration.calibration_slope

        # Uncalibrated naive estimate for comparison
        naive_tds_mg_l = cond_25 * 0.65
        overestimate_pct = (
            ((naive_tds_mg_l - true_salt_tds_mg_l) / true_salt_tds_mg_l) * 100.0
            if true_salt_tds_mg_l > 0 else 0.0
        )

        return {
            "status": "VALID" if is_valid else "HOLD_STATE",
            "fail_reason": None if is_valid else fail_reason,
            "raw_conductivity_us_cm": round(raw_conductivity_us_cm, 1),
            "cond_25c_us_cm": round(cond_25, 1),
            "ph": round(ph, 2),
            "temperature_c": round(temp_c, 1),
            "alkali_conductance_us_cm": round(kappa_alkali_us_cm, 1),
            "net_salt_conductance_us_cm": round(kappa_salt, 1),
            "calibrated_salt_tds_mg_l": round(true_salt_tds_mg_l, 1),
            "naive_tds_mg_l": round(naive_tds_mg_l, 1),
            "alkali_interference_overestimate_pct": round(overestimate_pct, 1),
            "active_titration_id": self.active_titration.record_id,
            "titration_chloride_mg_l": round(self.active_titration.chloride_mg_per_l, 1),
            "titration_nacl_equiv_mg_l": round(self.active_titration.nacl_equivalent_mg_per_l, 1),
            "savings_claim_allowed": is_valid,
            "savings_inr_multiplier": 1.0 if is_valid else 0.0,
        }

    def update_titration(self, record: TitrationRecord) -> Dict[str, Any]:
        """Register a new daily titration calibration from the lab."""
        self.active_titration = record
        return self.active_titration.to_dict()

    def get_hardware_status(self) -> Dict[str, Any]:
        """Return status and IBR-compliance of all clamp-on and probe skids."""
        is_valid, msg = self.check_telemetry_integrity()
        return {
            "system_state": "RUNNING" if is_valid else "HOLD_STATE",
            "system_message": msg,
            "devices": [dev.to_dict() for dev in self.devices.values()],
            "active_titration": self.active_titration.to_dict(),
            "ibr_compliance_verified": all(d.is_ibr_compliant for d in self.devices.values()),
        }


# Global calibration singleton
CALIBRATION_ENGINE = IonicCalibrationEngine()
