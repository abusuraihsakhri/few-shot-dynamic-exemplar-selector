"""
Additional security and edge case tests for Few Shot Dynamic Exemplar Selector.
Tests PHI guard patterns, audit trail integrity, input validation, and boundary conditions.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agents.base import PHIGuard, AuditTrail, SecurityException, assert_no_phi


class TestPHIGuardEdgeCases:
    """Test PHI guard against various sensitive data patterns."""

    def test_mrn_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient MRN-12345678")

    def test_ssn_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("SSN: 123-45-6789")

    def test_phone_number_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Call patient at 555-123-4567")

    def test_email_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Email results to doctor@hospital.org")

    def test_dob_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("DOB: 01/15/1985")

    def test_patient_name_detection(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient Name: John Smith")

    def test_generic_test_names(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Test for John Doe")

    def test_clean_text_passes(self):
        PHIGuard.assert_no_phi("Analytical specimen KEY-001 optimal")
        PHIGuard.assert_no_phi("Task completed successfully with metric 42.5")

    def test_empty_and_none_handling(self):
        PHIGuard.assert_no_phi("")
        PHIGuard.assert_no_phi(None)

    def test_redact_phi(self):
        text = "Patient MRN-12345 has SSN 123-45-6789"
        redacted = PHIGuard.redact_phi(text)
        assert "MRN" not in redacted or "REDACTED" in redacted
        assert "123-45-6789" not in redacted


class TestAuditTrailSecurity:
    """Test HMAC-SHA256 audit trail security properties."""

    def test_custom_secret_key(self):
        trail = AuditTrail(secret_key="test-secret-key-12345")
        entry = trail.log("test_actor", "test_tier", "TEST_EVENT", {"data": "value"})
        assert entry["current_hash"] != ""
        assert entry["prev_hash"] == "GENESIS_BLOCK_0000000000000000"

    def test_random_key_generation(self):
        """When no key is provided, a random key should be generated."""
        trail1 = AuditTrail()
        trail2 = AuditTrail()
        # Different instances should have different random keys
        assert trail1.secret_key != trail2.secret_key

    def test_phi_blocked_in_audit(self):
        trail = AuditTrail(secret_key="test-key")
        with pytest.raises(SecurityException):
            trail.log("actor", "tier", "EVENT", {"patient": "MRN-12345"})

    def test_tamper_detection(self):
        trail = AuditTrail(secret_key="test-key")
        trail.log("actor1", "tier1", "EVENT1", {"data": "value1"})
        trail.log("actor2", "tier2", "EVENT2", {"data": "value2"})

        assert trail.verify_integrity() is True

        # Simulate tampering
        trail.logs[0]["current_hash"] = "TAMPERED_HASH"
        assert trail.verify_integrity() is False

    def test_audit_chain_linking(self):
        trail = AuditTrail(secret_key="test-key")
        entry1 = trail.log("actor1", "tier1", "EVENT1", {"data": "value1"})
        entry2 = trail.log("actor2", "tier2", "EVENT2", {"data": "value2"})
        entry3 = trail.log("actor3", "tier3", "EVENT3", {"data": "value3"})

        assert entry2["prev_hash"] == entry1["current_hash"]
        assert entry3["prev_hash"] == entry2["current_hash"]


class TestInputValidation:
    """Test input validation and boundary conditions."""

    def test_extreme_metric_values(self):
        from agents.models import SystemTaskPayload
        from agents.supervisor import SystemSupervisor

        supervisor = SystemSupervisor(model_provider="mock")

        # Very large values
        payload = SystemTaskPayload(
            task_id="T-LARGE",
            target_identifier="KEY-01",
            primary_metric=999999.99,
            secondary_metric=999999.99,
        )
        dossier = supervisor.process_task(payload)
        assert dossier.overall_urgency.value in ["CRITICAL_STAT_PANIC", "ELEVATED_RISK"]

    def test_negative_metric_values(self):
        from agents.models import SystemTaskPayload
        from agents.supervisor import SystemSupervisor

        supervisor = SystemSupervisor(model_provider="mock")

        payload = SystemTaskPayload(
            task_id="T-NEG",
            target_identifier="KEY-01",
            primary_metric=-50.0,
            secondary_metric=-10.0,
        )
        dossier = supervisor.process_task(payload)
        assert dossier.overall_urgency.value == "ROUTINE"

    def test_zero_metric_values(self):
        from agents.models import SystemTaskPayload
        from agents.supervisor import SystemSupervisor

        supervisor = SystemSupervisor(model_provider="mock")

        payload = SystemTaskPayload(
            task_id="T-ZERO",
            target_identifier="KEY-01",
            primary_metric=0.0,
            secondary_metric=0.0,
        )
        dossier = supervisor.process_task(payload)
        assert dossier.overall_urgency.value == "ROUTINE"

    def test_special_characters_in_task_id(self):
        from agents.models import SystemTaskPayload
        from agents.supervisor import SystemSupervisor

        supervisor = SystemSupervisor(model_provider="mock")

        payload = SystemTaskPayload(
            task_id="TASK-@#$%^&*()",
            target_identifier="KEY-SPECIAL-!@#",
            primary_metric=10.0,
            secondary_metric=5.0,
        )
        dossier = supervisor.process_task(payload)
        assert dossier.task_id == "TASK-@#$%^&*()"


class TestBoundaryConditions:
    """Test threshold boundary conditions."""

    def test_primary_metric_at_threshold(self):
        from agents.models import SystemTaskPayload
        from agents.workers import InvariantQCWorker

        # Exactly at threshold (25.0) should not trigger
        payload = SystemTaskPayload(
            task_id="T-THRESHOLD",
            target_identifier="KEY-01",
            primary_metric=25.0,
        )
        alerts = InvariantQCWorker.evaluate(payload)
        assert len(alerts) == 0

    def test_primary_metric_just_above_threshold(self):
        from agents.models import SystemTaskPayload
        from agents.workers import InvariantQCWorker

        payload = SystemTaskPayload(
            task_id="T-ABOVE",
            target_identifier="KEY-01",
            primary_metric=25.01,
        )
        alerts = InvariantQCWorker.evaluate(payload)
        assert len(alerts) == 1

    def test_secondary_metric_at_threshold(self):
        from agents.models import SystemTaskPayload
        from agents.workers import SafetyEscalationWorker

        # Exactly at threshold (12.0) should not trigger
        payload = SystemTaskPayload(
            task_id="T-SEC",
            target_identifier="KEY-01",
            primary_metric=10.0,
            secondary_metric=12.0,
        )
        alerts = SafetyEscalationWorker.evaluate(payload)
        assert len(alerts) == 0

    def test_critical_flag_overrides_threshold(self):
        from agents.models import SystemTaskPayload
        from agents.workers import SafetyEscalationWorker

        payload = SystemTaskPayload(
            task_id="T-CRIT",
            target_identifier="KEY-01",
            primary_metric=10.0,
            secondary_metric=5.0,
            is_critical_flag=True,
        )
        alerts = SafetyEscalationWorker.evaluate(payload)
        assert len(alerts) == 1
        assert alerts[0].urgency.value == "CRITICAL_STAT_PANIC"
