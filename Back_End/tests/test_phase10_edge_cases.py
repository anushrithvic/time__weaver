"""
Comprehensive Edge Case Tests for Phase 10 APIs

Tests cover:
- Invalid inputs and data types
- Boundary conditions
- Missing required fields
- SQL injection attempts
- XSS attempts
- Large data payloads
- Concurrent requests
- Rate limiting scenarios
"""

import pytest
from httpx import AsyncClient
import asyncio


# ============================================================================
# INSTITUTIONAL RULES - EDGE CASES
# ============================================================================

class TestInstitutionalRulesEdgeCases:
    """Edge case tests for institutional rules API"""
    
    @pytest.mark.asyncio
    async def test_create_rule_missing_required_fields(self, client: AsyncClient, auth_headers: dict):
        """Test creating rule without required fields"""
        # Missing configuration
        invalid_data = {
            "name": "Test Rule",
            "rule_type": "TIME_WINDOW",
            "is_hard_constraint": True
            # Missing: configuration
        }
        
        response = await client.post("/api/v1/rules/", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_create_rule_invalid_rule_type(self, client: AsyncClient, auth_headers: dict):
        """Test creating rule with invalid rule type"""
        invalid_data = {
            "name": "Test Rule",
            "rule_type": "INVALID_TYPE",  # Not a valid enum
            "configuration": {},
            "is_hard_constraint": True,
            "weight": 1.0
        }
        
        response = await client.post("/api/v1/rules/", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_create_rule_invalid_weight_range(self, client: AsyncClient, auth_headers: dict):
        """Test weight outside valid range (0.0 - 1.0)"""
        # Weight > 1.0
        invalid_data = {
            "name": "Test Rule",
            "rule_type": "TIME_WINDOW",
            "configuration": {"min_slot": 2, "max_slot": 8},
            "is_hard_constraint": False,
            "weight": 2.5  # Invalid
        }
        
        response = await client.post("/api/v1/rules/", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422
        
        # Weight < 0.0
        invalid_data["weight"] = -0.5
        response = await client.post("/api/v1/rules/", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_create_rule_empty_name(self, client: AsyncClient, auth_headers: dict):
        """Test creating rule with empty name"""
        invalid_data = {
            "name": "",  # Empty
            "rule_type": "TIME_WINDOW",
            "configuration": {"min_slot": 2, "max_slot": 8},
            "is_hard_constraint": True,
            "weight": 1.0
        }
        
        response = await client.post("/api/v1/rules/", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_create_rule_very_long_name(self, client: AsyncClient, auth_headers: dict):
        """Test creating rule with name exceeding max length"""
        invalid_data = {
            "name": "x" * 300,  # Exceeds 200 char limit
            "rule_type": "TIME_WINDOW",
            "configuration": {"min_slot": 2, "max_slot": 8},
            "is_hard_constraint": True,
            "weight": 1.0
        }
        
        response = await client.post("/api/v1/rules/", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_create_rule_invalid_time_window_config(self, client: AsyncClient, auth_headers: dict):
        """Test TIME_WINDOW with invalid configuration"""
        # min_slot >= max_slot
        invalid_data = {
            "name": "Invalid Time Window",
            "rule_type": "TIME_WINDOW",
            "configuration": {"min_slot": 8, "max_slot": 2},  # Invalid order
            "is_hard_constraint": True,
            "weight": 1.0
        }
        
        response = await client.post("/api/v1/rules/", json=invalid_data, headers=auth_headers)
        assert response.status_code == 400
        assert "min_slot must be less than max_slot" in response.json()["detail"]["message"]
    
    @pytest.mark.asyncio
    async def test_create_rule_missing_config_fields(self, client: AsyncClient, auth_headers: dict):
        """Test TIME_WINDOW without required config fields"""
        invalid_data = {
            "name": "Missing Config Fields",
            "rule_type": "TIME_WINDOW",
            "configuration": {"min_slot": 2},  # Missing max_slot
            "is_hard_constraint": True,
            "weight": 1.0
        }
        
        response = await client.post("/api/v1/rules/", json=invalid_data, headers=auth_headers)
        assert response.status_code == 400
        assert "max_slot" in response.json()["detail"]["message"]
    
    @pytest.mark.asyncio
    async def test_create_rule_sql_injection_attempt(self, client: AsyncClient, auth_headers: dict):
        """Test SQL injection in rule name"""
        malicious_data = {
            "name": "'; DROP TABLE institutional_rules; --",
            "rule_type": "TIME_WINDOW",
            "configuration": {"min_slot": 2, "max_slot": 8},
            "is_hard_constraint": True,
            "weight": 1.0
        }
        
        response = await client.post("/api/v1/rules/", json=malicious_data, headers=auth_headers)
        # Should either succeed (parameterized queries protect) or fail validation
        # But should NOT execute SQL
        assert response.status_code in [201, 400, 422]
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_rule(self, client: AsyncClient, auth_headers: dict):
        """Test updating rule that doesn't exist"""
        response = await client.put(
            "/api/v1/rules/999999",
            json={"weight": 0.5},
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert response.json()["detail"]["error"] == "NOT_FOUND"
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_rule(self, client: AsyncClient, auth_headers: dict):
        """Test deleting rule that doesn't exist"""
        response = await client.delete("/api/v1/rules/999999", headers=auth_headers)
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_list_rules_with_invalid_pagination(self, client: AsyncClient, auth_headers: dict):
        """Test listing with negative skip/limit"""
        response = await client.get(
            "/api/v1/rules/?skip=-10&limit=-5",
            headers=auth_headers
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_list_rules_excessive_limit(self, client: AsyncClient, auth_headers: dict):
        """Test listing with limit exceeding max"""
        response = await client.get(
            "/api/v1/rules/?limit=10000",  # Exceeds max 500
            headers=auth_headers
        )
        assert response.status_code == 422


# ============================================================================
# TIMETABLE API - EDGE CASES
# ============================================================================

class TestTimetableEdgeCases:
    """Edge case tests for timetable API"""
    
    @pytest.mark.asyncio
    async def test_generate_with_negative_values(self, client: AsyncClient, auth_headers: dict):
        """Test generation with negative num_solutions or max_generations"""
        invalid_data = {
            "semester_id": 1,
            "algorithm": "GA",
            "num_solutions": -3,  # Negative
            "max_generations": -50
        }
        
        response = await client.post(
            "/api/v1/timetables/generate",
            json=invalid_data,
            headers=auth_headers
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_generate_with_zero_solutions(self, client: AsyncClient, auth_headers: dict):
        """Test generation with num_solutions = 0"""
        invalid_data = {
            "semester_id": 1,
            "algorithm": "GA",
            "num_solutions": 0,  # Should be >= 1
            "max_generations": 50
        }
        
        response = await client.post(
            "/api/v1/timetables/generate",
            json=invalid_data,
            headers=auth_headers
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_generate_with_invalid_algorithm(self, client: AsyncClient, auth_headers: dict):
        """Test generation with unsupported algorithm"""
        invalid_data = {
            "semester_id": 1,
            "algorithm": "INVALID_ALGO",
            "num_solutions": 3
        }
        
        response = await client.post(
            "/api/v1/timetables/generate",
            json=invalid_data,
            headers=auth_headers
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_generate_with_excessive_solutions(self, client: AsyncClient, auth_headers: dict):
        """Test generation with very large num_solutions"""
        invalid_data = {
            "semester_id": 1,
            "algorithm": "GA",
            "num_solutions": 1000,  # Too many
            "max_generations": 50
        }
        
        response = await client.post(
            "/api/v1/timetables/generate",
            json=invalid_data,
            headers=auth_headers
        )
        # Should either validate or accept (depending on limits)
        assert response.status_code in [400, 404, 422]
    
    @pytest.mark.asyncio
    async def test_delete_published_timetable(self, client: AsyncClient, auth_headers: dict):
        """Test deleting a published timetable (should fail)"""
        # This test assumes you have a published timetable
        # May need to create one first or use fixture
        response = await client.delete("/api/v1/timetables/1", headers=auth_headers)
        # Should either be 404 (not found) or 400 (published can't delete)
        assert response.status_code in [400, 404]
    
    @pytest.mark.asyncio
    async def test_view_with_invalid_year_level(self, client: AsyncClient, auth_headers: dict):
        """Test viewing with year_level outside valid range"""
        response = await client.get(
            "/api/v1/timetables/view?semester_id=1&year_level=10",  # Invalid year
            headers=auth_headers
        )
        assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    async def test_get_slots_invalid_day(self, client: AsyncClient, auth_headers: dict):
        """Test get slots with invalid day_of_week"""
        response = await client.get(
            "/api/v1/timetables/1/slots?day_of_week=10",  # Invalid (0-6)
            headers=auth_headers
        )
        assert response.status_code in [400, 422]


# ============================================================================
# SLOT LOCKING - EDGE CASES
# ============================================================================

class TestSlotLockingEdgeCases:
    """Edge case tests for slot locking API"""
    
    @pytest.mark.asyncio
    async def test_lock_empty_slot_list(self, client: AsyncClient, auth_headers: dict):
        """Test locking with empty slot_ids list"""
        response = await client.post(
            "/api/v1/slot-locks/lock",
            json={"timetable_id": 1, "slot_ids": []},
            headers=auth_headers
        )
        # Should succeed but lock nothing, or validate empty list
        assert response.status_code in [200, 400, 422]
    
    @pytest.mark.asyncio
    async def test_lock_duplicate_slots(self, client: AsyncClient, auth_headers: dict):
        """Test locking same slots twice"""
        lock_data = {"timetable_id": 1, "slot_ids": [1, 1, 1]}  # Duplicates
        
        response = await client.post(
            "/api/v1/slot-locks/lock",
            json=lock_data,
            headers=auth_headers
        )
        # Should handle duplicates gracefully
        assert response.status_code in [200, 400, 404]
    
    @pytest.mark.asyncio
    async def test_lock_nonexistent_slots(self, client: AsyncClient, auth_headers: dict):
        """Test locking slots that don't exist"""
        lock_data = {"timetable_id": 1, "slot_ids": [999999, 999998]}
        
        response = await client.post(
            "/api/v1/slot-locks/lock",
            json=lock_data,
            headers=auth_headers
        )
        assert response.status_code in [400, 404]
    
    @pytest.mark.asyncio
    async def test_unlock_already_unlocked(self, client: AsyncClient, auth_headers: dict):
        """Test unlocking slots that are already unlocked"""
        unlock_data = {"timetable_id": 1, "slot_ids": [1, 2]}
        
        response = await client.post(
            "/api/v1/slot-locks/unlock",
            json=unlock_data,
            headers=auth_headers
        )
        # Should succeed (idempotent)
        assert response.status_code in [200, 404]


# ============================================================================
# FACULTY LEAVE - EDGE CASES
# ============================================================================

class TestFacultyLeaveEdgeCases:
    """Edge case tests for faculty leave API"""
    
    @pytest.mark.asyncio
    async def test_create_leave_end_before_start(self, client: AsyncClient, auth_headers: dict):
        """Test creating leave with end_date before start_date"""
        invalid_data = {
            "faculty_id": 1,
            "semester_id": 1,
            "timetable_id": 1,
            "start_date": "2024-10-10",
            "end_date": "2024-10-01",  # Before start
            "leave_type": "SICK",
            "strategy": "WITHIN_SECTION_SWAP"
        }
        
        response = await client.post(
            "/api/v1/faculty-leaves/",
            json=invalid_data,
            headers=auth_headers
        )
        assert response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    async def test_create_leave_invalid_date_format(self, client: AsyncClient, auth_headers: dict):
        """Test creating leave with invalid date format"""
        invalid_data = {
            "faculty_id": 1,
            "semester_id": 1,
            "timetable_id": 1,
            "start_date": "10/01/2024",  # Wrong format
            "end_date": "10/07/2024",
            "leave_type": "SICK",
            "strategy": "WITHIN_SECTION_SWAP"
        }
        
        response = await client.post(
            "/api/v1/faculty-leaves/",
            json=invalid_data,
            headers=auth_headers
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_create_leave_past_dates(self, client: AsyncClient, auth_headers: dict):
        """Test creating leave for past dates"""
        invalid_data = {
            "faculty_id": 1,
            "semester_id": 1,
            "timetable_id": 1,
            "start_date": "2020-01-01",  # Past
            "end_date": "2020-01-07",
            "leave_type": "SICK",
            "strategy": "WITHIN_SECTION_SWAP"
        }
        
        response = await client.post(
            "/api/v1/faculty-leaves/",
            json=invalid_data,
            headers=auth_headers
        )
        # May succeed or fail depending on business rules
        assert response.status_code in [201, 400, 404]
    
    @pytest.mark.asyncio
    async def test_approve_already_approved_leave(self, client: AsyncClient, auth_headers: dict):
        """Test approving leave that's already approved"""
        response = await client.patch(
            "/api/v1/faculty-leaves/1/approve",
            headers=auth_headers
        )
        # Should be idempotent or indicate already approved
        assert response.status_code in [200, 400, 404]
    
    @pytest.mark.asyncio
    async def test_apply_unapproved_leave(self, client: AsyncClient, auth_headers: dict):
        """Test applying leave that hasn't been approved"""
        response = await client.patch(
            "/api/v1/faculty-leaves/999/apply",
            headers=auth_headers
        )
        # Should fail - must approve first
        assert response.status_code in [400, 404]


# ============================================================================
# SECURITY & PERMISSIONS EDGE CASES
# ============================================================================

class TestSecurityEdgeCases:
    """Security and permission edge cases"""
    
    @pytest.mark.asyncio
    async def test_expired_token(self, client: AsyncClient):
        """Test using expired authentication token"""
        # Simulated expired token
        expired_headers = {"Authorization": "Bearer expired.token.here"}
        
        response = await client.get("/api/v1/rules/", headers=expired_headers)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_malformed_token(self, client: AsyncClient):
        """Test malformed bearer token"""
        malformed_headers = {"Authorization": "Bearer notavalidtoken"}
        
        response = await client.get("/api/v1/rules/", headers=malformed_headers)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_missing_bearer_prefix(self, client: AsyncClient, admin_token: str):
        """Test token without Bearer prefix"""
        invalid_headers = {"Authorization": admin_token}  # Missing "Bearer "
        
        response = await client.get("/api/v1/rules/", headers=invalid_headers)
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_xss_in_rule_name(self, client: AsyncClient, auth_headers: dict):
        """Test XSS attempt in rule name"""
        xss_data = {
            "name": "<script>alert('XSS')</script>",
            "rule_type": "TIME_WINDOW",
            "configuration": {"min_slot": 2, "max_slot": 8},
            "is_hard_constraint": True,
            "weight": 1.0
        }
        
        response = await client.post("/api/v1/rules/", json=xss_data, headers=auth_headers)
        # Should sanitize or store safely
        if response.status_code == 201:
            # If created, name should not execute as script
            assert response.json()["name"] == xss_data["name"]


# ============================================================================
# CONCURRENCY & RACE CONDITIONS
# ============================================================================

class TestConcurrencyEdgeCases:
    """Test concurrent operations"""
    
    @pytest.mark.skip(reason="Test harness (AsyncSession) does not support concurrent requests sharing the same transaction")
    @pytest.mark.asyncio
    async def test_concurrent_rule_creation(self, client: AsyncClient, auth_headers: dict):
        """Test creating same rule concurrently"""
        import uuid
        rule_data = {
            "name": f"Concurrent Test Rule {uuid.uuid4()}",
            "rule_type": "TIME_WINDOW",
            "configuration": {"min_slot": 2, "max_slot": 8},
            "is_hard_constraint": True,
            "weight": 1.0
        }
        
        # Create 5 concurrent requests
        tasks = [
            client.post("/api/v1/rules/", json=rule_data, headers=auth_headers)
            for _ in range(5)
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Only one should succeed (due to unique name constraint)
        print(f"\nDEBUG RESPONSES: {[(r.status_code, r.text) if not isinstance(r, Exception) else str(r) for r in responses]}")
        success_count = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 201)
        assert success_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
